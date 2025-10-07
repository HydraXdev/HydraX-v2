"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  Target,
  TrendingUp,
  Shield,
  Zap,
  Clock,
  Award,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Star,
  Edit3,
  Save,
  Plus,
  Trash2,
  Brain,
  Lightbulb,
  BarChart3,
  Eye,
  FileText,
  Bookmark,
} from "lucide-react";

interface NotebookEntry {
  id: string;
  title: string;
  content: string;
  category: "trade" | "pattern" | "lesson" | "insight";
  timestamp: number;
  tags: string[];
}

interface LoreEntry {
  id: string;
  title: string;
  content: string;
  category: "pattern" | "strategy" | "psychology" | "risk";
  difficulty: "ROOKIE" | "SPECIALIST" | "ELITE" | "COMMANDER";
  readTime: number;
  completed: boolean;
}

export default function NotebookPage() {
  const [activeTab, setActiveTab] = useState<
    "norman" | "training" | "journal" | "tips"
  >("norman");
  const [expandedLore, setExpandedLore] = useState<string[]>([]);
  const [editingEntry, setEditingEntry] = useState<string | null>(null);
  const [newEntryTitle, setNewEntryTitle] = useState("");
  const [newEntryContent, setNewEntryContent] = useState("");

  // Norman's Notebook - Lore entries
  const loreEntries: LoreEntry[] = [
    {
      id: "1",
      title: "Liquidity Sweep Reversals",
      content:
        "Institutional traders often trigger stop losses below support or above resistance to collect liquidity before reversing. Look for wicks that extend beyond key levels followed by strong rejection candles. The best entries occur when price sweeps liquidity and immediately reverses with volume confirmation.",
      category: "pattern",
      difficulty: "SPECIALIST",
      readTime: 3,
      completed: true,
    },
    {
      id: "2",
      title: "Order Block Theory",
      content:
        "Order blocks represent areas where institutions placed large orders that moved price significantly. These zones often act as future support or resistance. Identify them by looking for the last opposite-colored candle before a strong directional move. Price often returns to these zones for retests.",
      category: "pattern",
      difficulty: "ELITE",
      readTime: 5,
      completed: false,
    },
    {
      id: "3",
      title: "Fair Value Gap Strategy",
      content:
        "Fair Value Gaps (FVGs) are inefficiencies in price action where gaps appear between candle bodies. Institutions typically fill these gaps over time. Look for 3-candle formations where the middle candle creates a gap that doesn't overlap with surrounding candles.",
      category: "pattern",
      difficulty: "SPECIALIST",
      readTime: 4,
      completed: true,
    },
    {
      id: "4",
      title: "Risk Management Fundamentals",
      content:
        "Never risk more than 2% per trade and 6% per day. Position sizing should be calculated as: Risk Amount ÷ (Stop Loss Distance in Pips × Pip Value). Always define your stop loss before entry. Use the 3R rule: Only take trades with minimum 3:1 reward-to-risk ratio.",
      category: "risk",
      difficulty: "ROOKIE",
      readTime: 6,
      completed: true,
    },
    {
      id: "5",
      title: "Psychology of Elite Trading",
      content:
        "Trading is 80% psychology, 20% strategy. Develop emotional discipline through meditation and journaling. Never revenge trade after losses. Take breaks after 3 consecutive losses. Remember: losses are the cost of doing business, not personal failures.",
      category: "psychology",
      difficulty: "COMMANDER",
      readTime: 8,
      completed: false,
    },
  ];

  // Training modules
  const trainingModules = [
    {
      id: "1",
      title: "Smart Money Concepts Basics",
      lessons: 12,
      completed: 8,
      category: "Foundation",
    },
    {
      id: "2",
      title: "Advanced Pattern Recognition",
      lessons: 8,
      completed: 3,
      category: "Patterns",
    },
    {
      id: "3",
      title: "Risk Management Mastery",
      lessons: 6,
      completed: 6,
      category: "Risk",
    },
    {
      id: "4",
      title: "Trading Psychology",
      lessons: 10,
      completed: 2,
      category: "Mental Game",
    },
  ];

  // User journal entries
  const [journalEntries, setJournalEntries] = useState<NotebookEntry[]>([
    {
      id: "1",
      title: "EURUSD Breakout Analysis",
      content:
        "Great trade today on EURUSD. The liquidity sweep at 1.0945 was textbook - price spiked through resistance, triggered stops, then immediately reversed. Entry at the retest gave us 45 pips to the upside. Key lesson: Wait for the sweep and rejection before entering.",
      category: "trade",
      timestamp: Date.now() - 3600000,
      tags: ["EURUSD", "Liquidity Sweep", "Breakout"],
    },
    {
      id: "2",
      title: "Session Notes - London Open",
      content:
        "London session showing high volatility today. GBPJPY particularly active with multiple order block retests. Notice how price respects the 195.50 level - this has been acting as strong resistance for 3 days now.",
      category: "insight",
      timestamp: Date.now() - 7200000,
      tags: ["London Session", "GBPJPY", "Order Blocks"],
    },
  ]);

  // Bit's Tips
  const bitsTips = [
    {
      id: "1",
      icon: Target,
      title: "Pattern Confluence",
      tip: "The best trades happen when multiple patterns align. Look for liquidity sweeps near order blocks during high-volume sessions.",
      category: "Strategy",
    },
    {
      id: "2",
      icon: Clock,
      title: "Timing is Everything",
      tip: "London and New York overlaps (12-16 UTC) provide the highest probability setups due to increased institutional activity.",
      category: "Timing",
    },
    {
      id: "3",
      icon: Shield,
      title: "Risk First",
      tip: "Always calculate your position size based on your stop loss, not your desired profit. Risk management keeps you in the game.",
      category: "Risk",
    },
    {
      id: "4",
      icon: Brain,
      title: "Journal Everything",
      tip: "Document every trade - wins, losses, and missed opportunities. Patterns in your behavior become visible over time.",
      category: "Psychology",
    },
  ];

  const toggleLore = (id: string) => {
    setExpandedLore((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  };

  const addJournalEntry = () => {
    if (newEntryTitle && newEntryContent) {
      const newEntry: NotebookEntry = {
        id: Date.now().toString(),
        title: newEntryTitle,
        content: newEntryContent,
        category: "trade",
        timestamp: Date.now(),
        tags: [],
      };
      setJournalEntries([newEntry, ...journalEntries]);
      setNewEntryTitle("");
      setNewEntryContent("");
    }
  };

  const deleteEntry = (id: string) => {
    setJournalEntries((prev) => prev.filter((entry) => entry.id !== id));
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "ROOKIE":
        return "text-mint";
      case "SPECIALIST":
        return "text-cyan";
      case "ELITE":
        return "text-warning";
      case "COMMANDER":
        return "text-danger";
      default:
        return "text-secondary";
    }
  };

  return (
    <div className="min-h-screen bg-primary text-primary">
      {/* Military HUD Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-active backdrop-blur-sm bg-overlay/30 sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <BookOpen className="w-8 h-8 text-mint pulse-glow" />
              <div>
                <h1 className="text-2xl font-tactical text-mint neon-glow">
                  Notebook & Training
                </h1>
                <p className="text-sm text-secondary font-code">
                  Education • Lore • Journaling
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Tab Navigation */}
              <div className="flex bg-secondary/50 rounded-lg p-1">
                {[
                  { key: "norman", label: "Norman's Notes", icon: BookOpen },
                  { key: "training", label: "Training", icon: Award },
                  { key: "journal", label: "My Journal", icon: Edit3 },
                  { key: "tips", label: "Bit's Tips", icon: Lightbulb },
                ].map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key as any)}
                    className={`px-4 py-2 rounded-md font-tactical text-sm transition-all flex items-center space-x-2 ${
                      activeTab === key
                        ? "bg-mint text-black"
                        : "text-secondary hover:text-primary"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {/* Norman's Notebook Tab */}
          {activeTab === "norman" && (
            <motion.div
              key="norman"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="hud-panel-accent p-6">
                <h2 className="text-xl font-tactical text-mint mb-2">
                  Norman's Trading Wisdom
                </h2>
                <p className="text-secondary">
                  Curated insights from years of institutional trading
                  experience. Master these concepts to elevate your trading.
                </p>
              </div>

              <div className="space-y-4">
                {loreEntries.map((entry, index) => (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="hud-panel p-6"
                  >
                    <div
                      className="cursor-pointer"
                      onClick={() => toggleLore(entry.id)}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-4">
                          <div
                            className={`px-3 py-1 rounded font-tactical text-xs ${getDifficultyColor(entry.difficulty)} border`}
                          >
                            {entry.difficulty}
                          </div>
                          <h3 className="text-lg font-tactical text-mint">
                            {entry.title}
                          </h3>
                          {entry.completed && (
                            <div className="w-6 h-6 bg-mint/20 rounded-full flex items-center justify-center">
                              <Star className="w-4 h-4 text-mint" />
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-4">
                          <span className="text-xs text-secondary">
                            {entry.readTime} min read
                          </span>
                          {expandedLore.includes(entry.id) ? (
                            <ChevronUp className="w-5 h-5 text-mint" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-secondary" />
                          )}
                        </div>
                      </div>
                    </div>

                    <AnimatePresence>
                      {expandedLore.includes(entry.id) && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="pt-4 border-t border-active">
                            <p className="text-secondary leading-relaxed mb-4">
                              {entry.content}
                            </p>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <span className="text-xs text-muted">
                                  Category:
                                </span>
                                <span className="text-xs text-cyan font-tactical">
                                  {entry.category.toUpperCase()}
                                </span>
                              </div>
                              {!entry.completed && (
                                <button className="btn-secondary text-sm py-1 px-3">
                                  <Bookmark className="w-4 h-4 mr-1" />
                                  Mark Complete
                                </button>
                              )}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Training Tab */}
          {activeTab === "training" && (
            <motion.div
              key="training"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="hud-panel-accent p-6">
                <h2 className="text-xl font-tactical text-mint mb-2">
                  Training Modules
                </h2>
                <p className="text-secondary">
                  Structured learning paths to master institutional trading
                  concepts.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {trainingModules.map((module, index) => (
                  <motion.div
                    key={module.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="hud-panel p-6 hover:border-mint/50 transition-all cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm text-warning font-tactical">
                        {module.category}
                      </div>
                      <div className="text-xs text-secondary">
                        {module.completed}/{module.lessons} lessons
                      </div>
                    </div>

                    <h3 className="text-lg font-tactical text-mint mb-3">
                      {module.title}
                    </h3>

                    <div className="mb-4">
                      <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-mint to-cyan transition-all duration-500"
                          style={{
                            width: `${(module.completed / module.lessons) * 100}%`,
                          }}
                        />
                      </div>
                      <div className="text-xs text-secondary mt-1">
                        {((module.completed / module.lessons) * 100).toFixed(0)}
                        % Complete
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-secondary">
                        {module.lessons - module.completed} lessons remaining
                      </span>
                      <button className="btn-secondary text-sm">
                        {module.completed === 0 ? "Start Module" : "Continue"}
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Journal Tab */}
          {activeTab === "journal" && (
            <motion.div
              key="journal"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="hud-panel-accent p-6">
                <h2 className="text-xl font-tactical text-mint mb-2">
                  Trading Journal
                </h2>
                <p className="text-secondary">
                  Document your trades, insights, and lessons learned.
                  Consistent journaling improves performance.
                </p>
              </div>

              {/* Add New Entry */}
              <div className="hud-panel p-6">
                <h3 className="text-lg font-tactical text-cyan mb-4">
                  New Entry
                </h3>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Entry title..."
                    value={newEntryTitle}
                    onChange={(e) => setNewEntryTitle(e.target.value)}
                    className="w-full p-3 bg-secondary border border-active rounded-lg text-primary placeholder-muted focus:border-mint transition-colors"
                  />
                  <textarea
                    placeholder="Write your thoughts, trade analysis, or lessons learned..."
                    value={newEntryContent}
                    onChange={(e) => setNewEntryContent(e.target.value)}
                    rows={4}
                    className="w-full p-3 bg-secondary border border-active rounded-lg text-primary placeholder-muted focus:border-mint transition-colors resize-none"
                  />
                  <button
                    onClick={addJournalEntry}
                    disabled={!newEntryTitle || !newEntryContent}
                    className="btn-primary"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Entry
                  </button>
                </div>
              </div>

              {/* Journal Entries */}
              <div className="space-y-4">
                {journalEntries.map((entry, index) => (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="hud-panel p-6"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="text-lg font-tactical text-mint">
                          {entry.title}
                        </h3>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className="text-xs text-secondary">
                            {new Date(entry.timestamp).toLocaleDateString()}
                          </span>
                          <div
                            className={`text-xs px-2 py-1 rounded ${
                              entry.category === "trade"
                                ? "bg-mint/20 text-mint"
                                : entry.category === "pattern"
                                  ? "bg-cyan/20 text-cyan"
                                  : entry.category === "lesson"
                                    ? "bg-warning/20 text-warning"
                                    : "bg-secondary/50 text-secondary"
                            }`}
                          >
                            {entry.category.toUpperCase()}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => deleteEntry(entry.id)}
                        className="text-danger hover:text-danger/80 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <p className="text-secondary leading-relaxed mb-3">
                      {entry.content}
                    </p>

                    {entry.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {entry.tags.map((tag, tagIndex) => (
                          <span
                            key={tagIndex}
                            className="text-xs px-2 py-1 bg-overlay rounded text-muted"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Bit's Tips Tab */}
          {activeTab === "tips" && (
            <motion.div
              key="tips"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="hud-panel-accent p-6">
                <h2 className="text-xl font-tactical text-mint mb-2">
                  Bit's Trading Tips
                </h2>
                <p className="text-secondary">
                  Quick insights and reminders from our AI trading assistant to
                  keep you sharp.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {bitsTips.map((tip, index) => {
                  const IconComponent = tip.icon;
                  return (
                    <motion.div
                      key={tip.id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="hud-panel p-6"
                    >
                      <div className="flex items-start space-x-4">
                        <div className="w-12 h-12 bg-mint/20 rounded-lg flex items-center justify-center border border-mint/30">
                          <IconComponent className="w-6 h-6 text-mint" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="font-tactical text-mint">
                              {tip.title}
                            </h3>
                            <span className="text-xs text-warning font-tactical">
                              {tip.category}
                            </span>
                          </div>
                          <p className="text-secondary text-sm leading-relaxed">
                            {tip.tip}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
