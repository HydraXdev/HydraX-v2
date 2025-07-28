"""
Specialized Attention Mechanisms for Financial Pattern Recognition

This module implements various attention mechanisms optimized for recognizing
patterns in financial time series data.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, Dict
import math

class LocalAttention(nn.Module):
    """
    Local attention mechanism that focuses on nearby time steps.
    Useful for capturing short-term patterns and momentum.
    """
    
    def __init__(self, d_model: int, window_size: int = 10, dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.window_size = window_size
        
        self.query = nn.Linear(d_model, d_model)
        self.key = nn.Linear(d_model, d_model)
        self.value = nn.Linear(d_model, d_model)
        self.output = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size, seq_len, _ = x.size()
        
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)
        
        # Create local attention mask
        mask = self._create_local_mask(seq_len, self.window_size).to(x.device)
        
        # Compute attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_model)
        scores = scores.masked_fill(mask == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # Apply attention
        context = torch.matmul(attention_weights, V)
        output = self.output(context)
        
        return output, attention_weights
    
    def _create_local_mask(self, seq_len: int, window_size: int) -> torch.Tensor:
        """Create a mask for local attention."""
        mask = torch.zeros(seq_len, seq_len)
        for i in range(seq_len):
            start = max(0, i - window_size // 2)
            end = min(seq_len, i + window_size // 2 + 1)
            mask[i, start:end] = 1
        return mask.unsqueeze(0)

class DilatedAttention(nn.Module):
    """
    Dilated attention mechanism that attends to time steps at different intervals.
    Captures patterns at multiple time scales efficiently.
    """
    
    def __init__(self, d_model: int, dilation_rates: list = [1, 2, 4, 8], dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.dilation_rates = dilation_rates
        
        self.query = nn.Linear(d_model, d_model)
        self.key = nn.Linear(d_model, d_model)
        self.value = nn.Linear(d_model, d_model)
        
        # Separate projection for each dilation rate
        self.rate_projections = nn.ModuleList([
            nn.Linear(d_model, d_model) for _ in dilation_rates
        ])
        
        self.output = nn.Linear(d_model * len(dilation_rates), d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size, seq_len, _ = x.size()
        
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)
        
        dilated_outputs = []
        all_attention_weights = []
        
        for rate, projection in zip(self.dilation_rates, self.rate_projections):
            # Create dilated attention mask
            mask = self._create_dilated_mask(seq_len, rate).to(x.device)
            
            # Compute attention scores
            scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_model)
            scores = scores.masked_fill(mask == 0, -1e9)
            
            attention_weights = F.softmax(scores, dim=-1)
            attention_weights = self.dropout(attention_weights)
            all_attention_weights.append(attention_weights)
            
            # Apply attention
            context = torch.matmul(attention_weights, V)
            dilated_output = projection(context)
            dilated_outputs.append(dilated_output)
        
        # Combine dilated attention outputs
        combined = torch.cat(dilated_outputs, dim=-1)
        output = self.output(combined)
        
        # Average attention weights across dilation rates
        avg_attention = torch.stack(all_attention_weights, dim=0).mean(dim=0)
        
        return output, avg_attention
    
    def _create_dilated_mask(self, seq_len: int, dilation_rate: int) -> torch.Tensor:
        """Create a mask for dilated attention."""
        mask = torch.zeros(seq_len, seq_len)
        for i in range(seq_len):
            for j in range(0, seq_len, dilation_rate):
                if j <= i:
                    mask[i, j] = 1
        return mask.unsqueeze(0)

class ProbabilisticAttention(nn.Module):
    """
    Probabilistic attention that models uncertainty in attention weights.
    Useful for handling noisy financial data.
    """
    
    def __init__(self, d_model: int, n_samples: int = 5, dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.n_samples = n_samples
        
        # Mean and variance networks for queries and keys
        self.query_mean = nn.Linear(d_model, d_model)
        self.query_logvar = nn.Linear(d_model, d_model)
        self.key_mean = nn.Linear(d_model, d_model)
        self.key_logvar = nn.Linear(d_model, d_model)
        
        self.value = nn.Linear(d_model, d_model)
        self.output = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
    
    def reparameterize(self, mean: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """Reparameterization trick for sampling."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mean + eps * std
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        batch_size, seq_len, _ = x.size()
        
        # Compute mean and variance for queries and keys
        q_mean = self.query_mean(x)
        q_logvar = self.query_logvar(x)
        k_mean = self.key_mean(x)
        k_logvar = self.key_logvar(x)
        
        V = self.value(x)
        
        # Sample multiple attention patterns
        sampled_outputs = []
        sampled_weights = []
        
        for _ in range(self.n_samples):
            # Sample queries and keys
            Q = self.reparameterize(q_mean, q_logvar)
            K = self.reparameterize(k_mean, k_logvar)
            
            # Compute attention scores
            scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_model)
            attention_weights = F.softmax(scores, dim=-1)
            attention_weights = self.dropout(attention_weights)
            sampled_weights.append(attention_weights)
            
            # Apply attention
            context = torch.matmul(attention_weights, V)
            sampled_outputs.append(context)
        
        # Aggregate samples
        mean_output = torch.stack(sampled_outputs, dim=0).mean(dim=0)
        var_output = torch.stack(sampled_outputs, dim=0).var(dim=0)
        mean_weights = torch.stack(sampled_weights, dim=0).mean(dim=0)
        
        output = self.output(mean_output)
        
        return output, mean_weights, var_output

class CrossTimeScaleAttention(nn.Module):
    """
    Cross-time-scale attention that allows information flow between different temporal resolutions.
    Captures both micro and macro market patterns.
    """
    
    def __init__(self, d_model: int, scales: list = [1, 5, 10, 20], dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.scales = scales
        
        # Downsampling layers for each scale
        self.downsamplers = nn.ModuleList([
            nn.Conv1d(d_model, d_model, kernel_size=scale, stride=scale)
            if scale > 1 else nn.Identity()
            for scale in scales
        ])
        
        # Cross-scale attention modules
        self.scale_attentions = nn.ModuleList([
            nn.MultiheadAttention(d_model, num_heads=4, dropout=dropout)
            for _ in scales
        ])
        
        # Scale combination
        self.scale_combination = nn.Linear(d_model * len(scales), d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        batch_size, seq_len, d_model = x.size()
        
        # Process each time scale
        scale_representations = []
        attention_maps = {}
        
        for i, (scale, downsampler, attention) in enumerate(
            zip(self.scales, self.downsamplers, self.scale_attentions)
        ):
            # Downsample if necessary
            if isinstance(downsampler, nn.Conv1d):
                x_scaled = downsampler(x.transpose(1, 2)).transpose(1, 2)
            else:
                x_scaled = x
            
            # Apply self-attention at this scale
            x_scaled = x_scaled.transpose(0, 1)  # (seq_len, batch, d_model)
            attn_output, attn_weights = attention(x_scaled, x_scaled, x_scaled)
            x_scaled = attn_output.transpose(0, 1)  # (batch, seq_len, d_model)
            
            # Upsample back to original resolution
            if x_scaled.size(1) != seq_len:
                x_scaled = F.interpolate(
                    x_scaled.transpose(1, 2),
                    size=seq_len,
                    mode='linear',
                    align_corners=False
                ).transpose(1, 2)
            
            scale_representations.append(x_scaled)
            attention_maps[f'scale_{scale}'] = attn_weights
        
        # Combine representations from all scales
        combined = torch.cat(scale_representations, dim=-1)
        output = self.scale_combination(combined)
        output = self.dropout(output)
        
        return output, attention_maps

class PatternMatchingAttention(nn.Module):
    """
    Pattern matching attention that learns to recognize specific market patterns.
    Uses learnable pattern templates.
    """
    
    def __init__(
        self, 
        d_model: int, 
        n_patterns: int = 32,
        pattern_length: int = 20,
        dropout: float = 0.1
    ):
        super().__init__()
        self.d_model = d_model
        self.n_patterns = n_patterns
        self.pattern_length = pattern_length
        
        # Learnable pattern templates
        self.patterns = nn.Parameter(torch.randn(n_patterns, pattern_length, d_model))
        
        # Pattern matching network
        self.pattern_query = nn.Linear(d_model, d_model)
        self.pattern_key = nn.Linear(d_model, d_model)
        self.pattern_value = nn.Linear(d_model, d_model)
        
        # Pattern combination
        self.pattern_weights = nn.Linear(n_patterns, 1)
        self.output = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size, seq_len, _ = x.size()
        
        # Prepare queries from input
        Q = self.pattern_query(x)  # (batch, seq_len, d_model)
        
        # Prepare keys and values from patterns
        K = self.pattern_key(self.patterns)  # (n_patterns, pattern_length, d_model)
        V = self.pattern_value(self.patterns)  # (n_patterns, pattern_length, d_model)
        
        # Compute attention between input and patterns
        pattern_matches = []
        
        for i in range(self.n_patterns):
            # Attention scores for pattern i
            scores = torch.matmul(Q, K[i].unsqueeze(0).transpose(-2, -1)) / math.sqrt(self.d_model)
            attention = F.softmax(scores, dim=-1)
            attention = self.dropout(attention)
            
            # Apply attention to pattern values
            context = torch.matmul(attention, V[i].unsqueeze(0).expand(batch_size, -1, -1))
            pattern_matches.append(context)
        
        # Stack pattern matches
        pattern_matches = torch.stack(pattern_matches, dim=2)  # (batch, seq_len, n_patterns, d_model)
        
        # Compute pattern importance weights
        pattern_importance = self.pattern_weights(
            pattern_matches.mean(dim=1).transpose(1, 2)
        ).squeeze(-1)  # (batch, n_patterns)
        pattern_importance = F.softmax(pattern_importance, dim=-1)
        
        # Weighted combination of pattern matches
        weighted_patterns = torch.einsum('bspd,bp->bsd', pattern_matches, pattern_importance)
        output = self.output(weighted_patterns)
        
        return output, pattern_importance

class HierarchicalAttention(nn.Module):
    """
    Hierarchical attention that processes data at multiple levels of abstraction.
    Useful for capturing market regimes and trends.
    """
    
    def __init__(
        self,
        d_model: int,
        segment_length: int = 10,
        n_heads: int = 4,
        dropout: float = 0.1
    ):
        super().__init__()
        self.d_model = d_model
        self.segment_length = segment_length
        
        # Intra-segment attention
        self.intra_attention = nn.MultiheadAttention(d_model, n_heads, dropout=dropout)
        
        # Segment representation
        self.segment_projection = nn.Linear(d_model, d_model)
        
        # Inter-segment attention
        self.inter_attention = nn.MultiheadAttention(d_model, n_heads, dropout=dropout)
        
        # Final projection
        self.output = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        batch_size, seq_len, d_model = x.size()
        
        # Pad sequence if necessary
        pad_len = (self.segment_length - seq_len % self.segment_length) % self.segment_length
        if pad_len > 0:
            x = F.pad(x, (0, 0, 0, pad_len))
            seq_len += pad_len
        
        n_segments = seq_len // self.segment_length
        
        # Reshape into segments
        x_segments = x.view(batch_size, n_segments, self.segment_length, d_model)
        
        # Apply intra-segment attention
        intra_outputs = []
        intra_weights = []
        
        for i in range(n_segments):
            segment = x_segments[:, i, :, :].transpose(0, 1)  # (seg_len, batch, d_model)
            attn_output, attn_weight = self.intra_attention(segment, segment, segment)
            intra_outputs.append(attn_output.transpose(0, 1))
            intra_weights.append(attn_weight)
        
        # Stack intra-segment outputs
        x_intra = torch.stack(intra_outputs, dim=1)  # (batch, n_segments, seg_len, d_model)
        
        # Create segment representations (average pooling)
        segment_reps = x_intra.mean(dim=2)  # (batch, n_segments, d_model)
        segment_reps = self.segment_projection(segment_reps)
        
        # Apply inter-segment attention
        segment_reps = segment_reps.transpose(0, 1)  # (n_segments, batch, d_model)
        inter_output, inter_weight = self.inter_attention(segment_reps, segment_reps, segment_reps)
        inter_output = inter_output.transpose(0, 1)  # (batch, n_segments, d_model)
        
        # Expand segment representations back to sequence length
        inter_expanded = inter_output.unsqueeze(2).expand(-1, -1, self.segment_length, -1)
        inter_expanded = inter_expanded.view(batch_size, seq_len, d_model)
        
        # Remove padding if added
        if pad_len > 0:
            inter_expanded = inter_expanded[:, :-pad_len, :]
        
        # Final output
        output = self.output(inter_expanded)
        output = self.dropout(output)
        
        attention_info = {
            'intra_weights': torch.stack(intra_weights, dim=1),
            'inter_weights': inter_weight
        }
        
        return output, attention_info