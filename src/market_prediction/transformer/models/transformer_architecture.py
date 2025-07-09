"""
Transformer Architecture for Market Time Series Prediction

This module implements a transformer-based architecture specifically designed
for financial time series prediction with attention mechanisms for pattern recognition.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional
import math


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer architecture."""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:x.size(0), :]


class MultiHeadAttentionWithScore(nn.Module):
    """Multi-head attention mechanism with attention score output for interpretability."""
    
    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0
        
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        
        self.linear_q = nn.Linear(d_model, d_model)
        self.linear_k = nn.Linear(d_model, d_model)
        self.linear_v = nn.Linear(d_model, d_model)
        self.linear_out = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
        self.attention_scores = None
    
    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size = query.size(0)
        seq_len = query.size(1)
        
        # Linear transformations and reshape
        Q = self.linear_q(query).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        K = self.linear_k(key).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = self.linear_v(value).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        
        # Attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        self.attention_scores = attention_weights.detach()
        
        attention_weights = self.dropout(attention_weights)
        
        # Apply attention to values
        context = torch.matmul(attention_weights, V)
        
        # Reshape and apply output projection
        context = context.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.d_model
        )
        output = self.linear_out(context)
        
        return output, attention_weights


class TransformerBlock(nn.Module):
    """Transformer encoder block with multi-head attention and feed-forward network."""
    
    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        
        self.attention = MultiHeadAttentionWithScore(d_model, n_heads, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        # Multi-head attention
        attn_output, attn_weights = self.attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        # Feed-forward network
        ff_output = self.feed_forward(x)
        x = self.norm2(x + ff_output)
        
        return x, attn_weights


class MarketTransformer(nn.Module):
    """
    Transformer model for market prediction with uncertainty estimation.
    
    Features:
    - Multi-head self-attention for pattern recognition
    - Positional encoding for temporal awareness
    - Multiple prediction heads for different time horizons
    - Uncertainty estimation through variance prediction
    """
    
    def __init__(
        self,
        input_dim: int,
        d_model: int = 512,
        n_heads: int = 8,
        n_layers: int = 6,
        d_ff: int = 2048,
        max_seq_len: int = 100,
        n_outputs: int = 1,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.d_model = d_model
        self.n_outputs = n_outputs
        
        # Input projection
        self.input_projection = nn.Linear(input_dim, d_model)
        
        # Positional encoding
        self.positional_encoding = PositionalEncoding(d_model, max_seq_len)
        
        # Transformer blocks
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])
        
        # Output heads
        self.prediction_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, n_outputs)
        )
        
        # Uncertainty estimation head
        self.uncertainty_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, n_outputs),
            nn.Softplus()  # Ensure positive variance
        )
        
        # Confidence scoring head
        self.confidence_head = nn.Sequential(
            nn.Linear(d_model, d_model // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 4, 1),
            nn.Sigmoid()  # Output between 0 and 1
        )
        
        self.dropout = nn.Dropout(dropout)
        self.attention_weights_history = []
    
    def create_padding_mask(self, x: torch.Tensor, lengths: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Create padding mask for variable length sequences."""
        if lengths is None:
            return None
        
        batch_size, max_len = x.size(0), x.size(1)
        mask = torch.arange(max_len).expand(batch_size, max_len).to(x.device)
        mask = mask < lengths.unsqueeze(1)
        return mask.unsqueeze(1).unsqueeze(2)
    
    def forward(
        self, 
        x: torch.Tensor, 
        lengths: Optional[torch.Tensor] = None,
        return_attention: bool = False
    ) -> dict:
        """
        Forward pass through the transformer.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_dim)
            lengths: Optional tensor of sequence lengths for masking
            return_attention: Whether to return attention weights
            
        Returns:
            Dictionary containing:
                - predictions: Point predictions
                - uncertainty: Uncertainty estimates (variance)
                - confidence: Confidence scores
                - attention_weights: Attention weights (if requested)
        """
        # Input projection and positional encoding
        x = self.input_projection(x)
        x = x.transpose(0, 1)  # (seq_len, batch_size, d_model)
        x = self.positional_encoding(x)
        x = self.dropout(x)
        
        # Create padding mask
        mask = self.create_padding_mask(x.transpose(0, 1), lengths)
        
        # Pass through transformer blocks
        attention_weights = []
        for transformer in self.transformer_blocks:
            x, attn_weights = transformer(x.transpose(0, 1), mask)
            x = x.transpose(0, 1)
            if return_attention:
                attention_weights.append(attn_weights)
        
        # Use the last hidden state for prediction
        x = x.transpose(0, 1)
        
        # Global average pooling over sequence dimension
        if lengths is not None:
            # Mask out padding positions
            mask_expanded = mask.squeeze(1).squeeze(1).unsqueeze(-1).float()
            x = (x * mask_expanded).sum(dim=1) / lengths.unsqueeze(-1).float()
        else:
            x = x.mean(dim=1)
        
        # Generate outputs
        predictions = self.prediction_head(x)
        uncertainty = self.uncertainty_head(x)
        confidence = self.confidence_head(x)
        
        outputs = {
            'predictions': predictions,
            'uncertainty': uncertainty,
            'confidence': confidence
        }
        
        if return_attention:
            outputs['attention_weights'] = attention_weights
        
        return outputs


class TemporalTransformer(MarketTransformer):
    """
    Extended transformer with temporal convolution layers for better time series modeling.
    """
    
    def __init__(self, *args, kernel_sizes: list = [3, 5, 7], **kwargs):
        super().__init__(*args, **kwargs)
        
        # Temporal convolution layers
        self.temporal_convs = nn.ModuleList([
            nn.Conv1d(self.d_model, self.d_model, kernel_size=k, padding=k//2)
            for k in kernel_sizes
        ])
        
        self.temporal_projection = nn.Linear(self.d_model * len(kernel_sizes), self.d_model)
    
    def forward(
        self, 
        x: torch.Tensor, 
        lengths: Optional[torch.Tensor] = None,
        return_attention: bool = False
    ) -> dict:
        """Forward pass with temporal convolutions."""
        # Input projection and positional encoding
        x = self.input_projection(x)
        batch_size, seq_len = x.size(0), x.size(1)
        
        # Apply temporal convolutions
        x_conv = x.transpose(1, 2)  # (batch, d_model, seq_len)
        conv_outputs = []
        for conv in self.temporal_convs:
            conv_outputs.append(F.relu(conv(x_conv)))
        
        # Concatenate and project back
        x_conv = torch.cat(conv_outputs, dim=1)  # (batch, d_model * n_convs, seq_len)
        x_conv = x_conv.transpose(1, 2)  # (batch, seq_len, d_model * n_convs)
        x_conv = self.temporal_projection(x_conv)
        
        # Add residual connection
        x = x + x_conv
        
        # Continue with standard transformer processing
        x = x.transpose(0, 1)  # (seq_len, batch_size, d_model)
        x = self.positional_encoding(x)
        x = self.dropout(x)
        
        # Create padding mask
        mask = self.create_padding_mask(x.transpose(0, 1), lengths)
        
        # Pass through transformer blocks
        attention_weights = []
        for transformer in self.transformer_blocks:
            x, attn_weights = transformer(x.transpose(0, 1), mask)
            x = x.transpose(0, 1)
            if return_attention:
                attention_weights.append(attn_weights)
        
        # Use the last hidden state for prediction
        x = x.transpose(0, 1)
        
        # Global average pooling over sequence dimension
        if lengths is not None:
            mask_expanded = mask.squeeze(1).squeeze(1).unsqueeze(-1).float()
            x = (x * mask_expanded).sum(dim=1) / lengths.unsqueeze(-1).float()
        else:
            x = x.mean(dim=1)
        
        # Generate outputs
        predictions = self.prediction_head(x)
        uncertainty = self.uncertainty_head(x)
        confidence = self.confidence_head(x)
        
        outputs = {
            'predictions': predictions,
            'uncertainty': uncertainty,
            'confidence': confidence
        }
        
        if return_attention:
            outputs['attention_weights'] = attention_weights
        
        return outputs