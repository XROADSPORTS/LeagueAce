import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Calendar, Users, Trophy, Settings, Plus, TrendingUp, Clock, MapPin, UserCheck, Shield, Code, Copy, Eye, EyeOff } from "lucide-react";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Badge } from "./components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentView, setCurrentView] = useState("signup");
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("home");
  
  // Data states
  const [mainSeasons, setMainSeasons] = useState([]);
  const [userJoinedTiers, setUserJoinedTiers] = useState([]);
  const [userStandings, setUserStandings] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadManagerData = async () => {
    if (user && user.role === "League Manager") {
      try {
        const response = await axios.get(`${API}/users/${user.id}/main-seasons`);
        setMainSeasons(response.data);
      } catch (error) {
        console.error("Error loading manager data:", error);
      }
    }
  };

  const loadPlayerData = async () => {
    if (user && user.role === "Player") {
      try {
        const [joinedTiersRes, standingsRes] = await Promise.all([
          axios.get(`${API}/users/${user.id}/joined-tiers`),
          axios.get(`${API}/users/${user.id}/standings`)
        ]);
        setUserJoinedTiers(joinedTiersRes.data);
        setUserStandings(standingsRes.data);
      } catch (error) {
        console.error("Error loading player data:", error);
      }
    }
  };

  useEffect(() => {
    if (user) {
      if (user.role === "League Manager") {
        loadManagerData();
      } else if (user.role === "Player") {
        loadPlayerData();
      }
    }
  }, [user]);

  // Signup Component
  const SignupView = () => {
    const [signupType, setSignupType] = useState(null);

    const SignupOptions = () => (
      <div className="signup-container">
        <div className="signup-hero">
          <h1 className="signup-title">
            Join <span className="gradient-text">Netly</span>
          </h1>
          <p className="signup-subtitle">
            Choose how you want to participate in tennis & pickleball leagues
          </p>
        </div>
        
        <div className="signup-options">
          <Card 
            className="glass-card signup-option-card"
            onClick={() => setSignupType("player")}
          >
            <CardContent className="signup-option-content">
              <UserCheck className="signup-option-icon" />
              <h3>Join as Player</h3>
              <p>Join leagues, play matches, and compete for rankings</p>
              <ul className="signup-benefits">
                <li>Join multiple league tiers</li>
                <li>Track your performance</li>
                <li>View live standings</li>
                <li>Schedule matches</li>
              </ul>
            </CardContent>
          </Card>

          <Card 
            className="glass-card signup-option-card"
            onClick={() => setSignupType("manager")}
          >
            <CardContent className="signup-option-content">
              <Shield className="signup-option-icon" />
              <h3>Become League Manager</h3>
              <p>Create and manage comprehensive league structures</p>
              <ul className="signup-benefits">
                <li>Create seasonal leagues</li>
                <li>Manage player tiers</li>
                <li>Generate unique join codes</li>
                <li>Full administrative control</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    );

    const SignupForm = ({ role }) => {
      const [formData, setFormData] = useState({
        name: "",
        email: "",
        phone: "",
        rating_level: 4.0,
        role: role
      });

      const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
          const response = await axios.post(`${API}/users`, formData);
          setUser(response.data);
          setCurrentView("dashboard");
          setActiveTab("home");
        } catch (error) {
          console.error("Error creating user:", error);
        }
        setLoading(false);
      };

      return (
        <div className="signup-form-container">
          <Button 
            variant="ghost" 
            onClick={() => setSignupType(null)}
            className="back-button"
          >
            ← Back to Options
          </Button>
          
          <Card className="glass-card signup-form-card">
            <CardHeader>
              <CardTitle className="gradient-text">
                Sign up as {role === "Player" ? "Player" : "League Manager"}
              </CardTitle>
              <CardDescription>
                {role === "Player" 
                  ? "Create your player profile to join leagues" 
                  : "Set up your account to manage tennis & pickleball leagues"
                }
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="phone">Phone Number (Optional)</Label>
                  <Input
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                <div>
                  <Label htmlFor="rating">Current Skill Rating (3.0-5.5)</Label>
                  <Input
                    id="rating"
                    type="number"
                    min="3.0"
                    max="5.5"
                    step="0.1"
                    value={formData.rating_level}
                    onChange={(e) => setFormData({...formData, rating_level: parseFloat(e.target.value)})}
                    required
                  />
                  <p className="rating-help">
                    Rate yourself honestly: 3.0 = Beginner, 4.0 = Intermediate, 5.0+ = Advanced
                  </p>
                </div>
              </CardContent>
              <CardFooter>
                <Button type="submit" className="sport-button w-full" disabled={loading}>
                  {loading ? "Creating Account..." : `Create ${role} Account`}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      );
    };

    if (!signupType) {
      return <SignupOptions />;
    }

    return <SignupForm role={signupType === "player" ? "Player" : "League Manager"} />;
  };

  // League Manager Components
  const LeagueManagerDashboard = () => {
    const [activeManagerTab, setActiveManagerTab] = useState("overview");
    const [showCreateSeason, setShowCreateSeason] = useState(false);

    const CreateSeasonForm = () => {
      const [seasonData, setSeasonData] = useState({
        name: "",
        description: "",
        start_date: "",
        end_date: ""
      });

      const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
          await axios.post(`${API}/main-seasons?created_by=${user.id}`, seasonData);
          loadManagerData();
          setShowCreateSeason(false);
          setSeasonData({ name: "", description: "", start_date: "", end_date: "" });
        } catch (error) {
          console.error("Error creating season:", error);
        }
        setLoading(false);
      };

      return (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Create New Main Season</CardTitle>
            <CardDescription>Set up a new seasonal league structure</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="season-name">Season Name</Label>
                <Input
                  id="season-name"
                  value={seasonData.name}
                  onChange={(e) => setSeasonData({...seasonData, name: e.target.value})}
                  placeholder="e.g., Season 14, Spring 2024"
                  required
                />
              </div>
              <div>
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  value={seasonData.description}
                  onChange={(e) => setSeasonData({...seasonData, description: e.target.value})}
                  placeholder="Describe this season..."
                />
              </div>
              <div className="date-row">
                <div>
                  <Label htmlFor="start-date">Start Date</Label>
                  <Input
                    id="start-date"
                    type="date"
                    value={seasonData.start_date}
                    onChange={(e) => setSeasonData({...seasonData, start_date: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="end-date">End Date</Label>
                  <Input
                    id="end-date"
                    type="date"
                    value={seasonData.end_date}
                    onChange={(e) => setSeasonData({...seasonData, end_date: e.target.value})}
                    required
                  />
                </div>
              </div>
            </CardContent>
            <CardFooter className="space-x-2">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setShowCreateSeason(false)}
              >
                Cancel
              </Button>
              <Button type="submit" className="sport-button" disabled={loading}>
                {loading ? "Creating..." : "Create Season"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      );
    };

    const SeasonManagement = () => {
      const [selectedSeason, setSelectedSeason] = useState(null);
      const [formatTiers, setFormatTiers] = useState([]);
      const [skillTiers, setSkillTiers] = useState([]);

      const loadFormatTiers = async (seasonId) => {
        try {
          const response = await axios.get(`${API}/main-seasons/${seasonId}/format-tiers`);
          setFormatTiers(response.data);
        } catch (error) {
          console.error("Error loading format tiers:", error);
        }
      };

      const createFormatTier = async (seasonId, name) => {
        try {
          await axios.post(`${API}/format-tiers`, {
            main_season_id: seasonId,
            name: name,
            description: `${name} format for this season`
          });
          loadFormatTiers(seasonId);
        } catch (error) {
          console.error("Error creating format tier:", error);
        }
      };

      const createSkillTier = async (formatTierId, tierData) => {
        try {
          await axios.post(`${API}/skill-tiers`, {
            format_tier_id: formatTierId,
            ...tierData
          });
          // Reload skill tiers
          const response = await axios.get(`${API}/format-tiers/${formatTierId}/skill-tiers`);
          setSkillTiers(response.data);
        } catch (error) {
          console.error("Error creating skill tier:", error);
        }
      };

      return (
        <div className="space-y-6">
          <div className="seasons-grid">
            {mainSeasons.map((season) => (
              <Card 
                key={season.id} 
                className={`glass-card season-card ${selectedSeason?.id === season.id ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedSeason(season);
                  loadFormatTiers(season.id);
                }}
              >
                <CardHeader>
                  <CardTitle>{season.name}</CardTitle>
                  <CardDescription>
                    {new Date(season.start_date).toLocaleDateString()} - 
                    {new Date(season.end_date).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Badge className="sport-badge">{season.status}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>

          {selectedSeason && (
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Manage {selectedSeason.name}</CardTitle>
                <CardDescription>Create and manage format tiers and skill levels</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="tier-management">
                  <div className="format-tiers">
                    <h4>Format Tiers</h4>
                    <div className="tier-buttons">
                      <Button 
                        className="sport-button"
                        onClick={() => createFormatTier(selectedSeason.id, "Singles")}
                      >
                        Add Singles
                      </Button>
                      <Button 
                        className="sport-button"
                        onClick={() => createFormatTier(selectedSeason.id, "Doubles")}
                      >
                        Add Doubles
                      </Button>
                    </div>
                    
                    <div className="format-tier-list">
                      {formatTiers.map((tier) => (
                        <FormatTierCard 
                          key={tier.id} 
                          tier={tier} 
                          onCreateSkillTier={createSkillTier}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      );
    };

    const FormatTierCard = ({ tier, onCreateSkillTier }) => {
      const [skillTiers, setSkillTiers] = useState([]);
      const [showSkillForm, setShowSkillForm] = useState(false);
      const [skillData, setSkillData] = useState({
        name: "",
        min_rating: 3.0,
        max_rating: 3.5,
        max_players: 36,
        region: "General",
        surface: "Hard Court"
      });

      useEffect(() => {
        loadSkillTiers();
      }, [tier.id]);

      const loadSkillTiers = async () => {
        try {
          const response = await axios.get(`${API}/format-tiers/${tier.id}/skill-tiers`);
          setSkillTiers(response.data);
        } catch (error) {
          console.error("Error loading skill tiers:", error);
        }
      };

      const handleCreateSkillTier = async (e) => {
        e.preventDefault();
        await onCreateSkillTier(tier.id, skillData);
        loadSkillTiers();
        setShowSkillForm(false);
        setSkillData({
          name: "",
          min_rating: 3.0,
          max_rating: 3.5,
          max_players: 36,
          region: "General",
          surface: "Hard Court"
        });
      };

      return (
        <Card className="glass-card format-tier-card">
          <CardHeader>
            <CardTitle>{tier.name}</CardTitle>
            <CardDescription>Skill level tiers for {tier.name}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="skill-tiers-grid">
              {skillTiers.map((skillTier) => (
                <Card key={skillTier.id} className="skill-tier-card">
                  <CardContent className="skill-tier-content">
                    <h5>{skillTier.name}</h5>
                    <p>Rating: {skillTier.min_rating} - {skillTier.max_rating}</p>
                    <div className="join-code-display">
                      <Code className="w-4 h-4" />
                      <span>{skillTier.join_code}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigator.clipboard?.writeText(skillTier.join_code)}
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                    <Badge variant="outline">{skillTier.max_players} max players</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            {!showSkillForm ? (
              <Button 
                className="sport-button mt-4"
                onClick={() => setShowSkillForm(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Skill Tier
              </Button>
            ) : (
              <form onSubmit={handleCreateSkillTier} className="skill-tier-form">
                <div className="form-row">
                  <div>
                    <Label>Tier Name</Label>
                    <Input
                      value={skillData.name}
                      onChange={(e) => setSkillData({...skillData, name: e.target.value})}
                      placeholder="e.g., 4.0, 4.5, 5.0"
                      required
                    />
                  </div>
                  <div>
                    <Label>Min Rating</Label>
                    <Input
                      type="number"
                      min="3.0"
                      max="5.5"
                      step="0.1"
                      value={skillData.min_rating}
                      onChange={(e) => setSkillData({...skillData, min_rating: parseFloat(e.target.value)})}
                      required
                    />
                  </div>
                  <div>
                    <Label>Max Rating</Label>
                    <Input
                      type="number"
                      min="3.0"
                      max="5.5"
                      step="0.1"
                      value={skillData.max_rating}
                      onChange={(e) => setSkillData({...skillData, max_rating: parseFloat(e.target.value)})}
                      required
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <Button type="button" variant="outline" onClick={() => setShowSkillForm(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" className="sport-button">
                    Create Tier
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      );
    };

    return (
      <div className="manager-dashboard">
        <div className="dashboard-header">
          <h2 className="section-title">League Manager Dashboard</h2>
          <div className="manager-stats">
            <Badge className="stat-badge">
              {mainSeasons.length} Seasons Created
            </Badge>
          </div>
        </div>

        <Tabs value={activeManagerTab} onValueChange={setActiveManagerTab}>
          <TabsList className="manager-tabs">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="seasons">Manage Seasons</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="manager-overview">
              {!showCreateSeason ? (
                <Card className="glass-card">
                  <CardContent className="create-season-prompt">
                    <Trophy className="prompt-icon" />
                    <h3>Ready to Create Your League Structure?</h3>
                    <p>Build comprehensive league hierarchies with seasons, formats, and skill tiers</p>
                    <Button 
                      className="sport-button"
                      onClick={() => setShowCreateSeason(true)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create New Season
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <CreateSeasonForm />
              )}
            </div>
          </TabsContent>

          <TabsContent value="seasons">
            <SeasonManagement />
          </TabsContent>
        </Tabs>
      </div>
    );
  };

  // Player Components
  const PlayerDashboard = () => {
    const [showJoinForm, setShowJoinForm] = useState(false);
    const [joinCode, setJoinCode] = useState("");

    const handleJoinByCode = async (e) => {
      e.preventDefault();
      setLoading(true);
      try {
        await axios.post(`${API}/join-by-code/${user.id}`, { join_code: joinCode });
        loadPlayerData();
        setShowJoinForm(false);
        setJoinCode("");
      } catch (error) {
        console.error("Error joining by code:", error);
        alert(error.response?.data?.detail || "Failed to join league");
      }
      setLoading(false);
    };

    const PlayerHome = () => (
      <div className="space-y-6">
        {/* Player Stats */}
        <div className="stats-grid">
          <Card className="glass-card stat-card">
            <CardContent className="p-6">
              <div className="stat-content">
                <Users className="stat-icon" />
                <div>
                  <p className="stat-number">{userJoinedTiers.length}</p>
                  <p className="stat-label">Leagues Joined</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="glass-card stat-card">
            <CardContent className="p-6">
              <div className="stat-content">
                <Trophy className="stat-icon" />
                <div>
                  <p className="stat-number">{userStandings.length}</p>
                  <p className="stat-label">Active Standings</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="glass-card stat-card">
            <CardContent className="p-6">
              <div className="stat-content">
                <TrendingUp className="stat-icon" />
                <div>
                  <p className="stat-number">{user.rating_level}</p>
                  <p className="stat-label">Current Rating</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Join League Section */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Join a League</CardTitle>
            <CardDescription>
              Enter a join code provided by your league manager to join a specific tier
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!showJoinForm ? (
              <Button 
                className="sport-button"
                onClick={() => setShowJoinForm(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                Join New League
              </Button>
            ) : (
              <form onSubmit={handleJoinByCode} className="join-form">
                <div className="join-input-group">
                  <Input
                    value={joinCode}
                    onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                    placeholder="Enter 6-character join code"
                    maxLength={6}
                    className="join-code-input"
                    required
                  />
                  <Button type="submit" className="sport-button" disabled={loading}>
                    {loading ? "Joining..." : "Join"}
                  </Button>
                </div>
                <Button 
                  type="button" 
                  variant="ghost" 
                  onClick={() => setShowJoinForm(false)}
                  className="cancel-join"
                >
                  Cancel
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        {/* My Leagues */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>My Leagues</CardTitle>
          </CardHeader>
          <CardContent>
            {userJoinedTiers.length > 0 ? (
              <div className="joined-tiers-grid">
                {userJoinedTiers.map((tierInfo) => (
                  <Card key={tierInfo.seat_id} className="joined-tier-card">
                    <CardContent className="joined-tier-content">
                      <div className="tier-hierarchy">
                        <h4>{tierInfo.main_season.name}</h4>
                        <p>{tierInfo.format_tier.name} • {tierInfo.skill_tier.name}</p>
                      </div>
                      <div className="tier-details">
                        <Badge 
                          className={tierInfo.status === "Active" ? "sport-badge" : "reserve-badge"}
                        >
                          {tierInfo.status}
                        </Badge>
                        <p className="tier-rating">
                          Rating: {tierInfo.skill_tier.min_rating} - {tierInfo.skill_tier.max_rating}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="no-leagues">No leagues joined yet. Use a join code to get started!</p>
            )}
          </CardContent>
        </Card>
      </div>
    );

    const PlayerStandings = () => (
      <div className="space-y-6">
        <h2 className="section-title">My Standings</h2>
        
        {userStandings.length > 0 ? (
          <div className="standings-grid">
            {userStandings.map((standingInfo) => (
              <Card key={standingInfo.standing.id} className="glass-card">
                <CardHeader>
                  <CardTitle>{standingInfo.skill_tier.name}</CardTitle>
                  <CardDescription>
                    Rating: {standingInfo.skill_tier.min_rating} - {standingInfo.skill_tier.max_rating}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="standing-stats">
                    <div className="stat-item">
                      <span className="stat-value">{standingInfo.standing.rank || "N/A"}</span>
                      <span className="stat-label">Rank</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{standingInfo.standing.total_set_wins}</span>
                      <span className="stat-label">Sets Won</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{standingInfo.standing.total_sets_played}</span>
                      <span className="stat-label">Sets Played</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">
                        {(standingInfo.standing.win_pct * 100).toFixed(1)}%
                      </span>
                      <span className="stat-label">Win Rate</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="glass-card">
            <CardContent className="p-8 text-center">
              <Trophy className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No standings yet</h3>
              <p className="text-muted-foreground">
                Your standings will appear here once you start playing matches
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    );

    return (
      <div className="player-dashboard">
        {activeTab === "home" && <PlayerHome />}
        {activeTab === "standings" && <PlayerStandings />}
      </div>
    );
  };

  const DashboardView = () => {
    if (!user) return null;

    return (
      <div className="app-container">
        {/* Navigation */}
        <nav className="nav-glass">
          <div className="nav-brand">
            <h1 className="nav-logo">Netly</h1>
          </div>
          
          {user.role === "League Manager" ? (
            <div className="nav-tabs">
              <Button
                variant={activeTab === "home" ? "default" : "ghost"}
                onClick={() => setActiveTab("home")}
                className="nav-button"
              >
                <Shield className="w-4 h-4 mr-2" />
                Dashboard
              </Button>
            </div>
          ) : (
            <div className="nav-tabs">
              <Button
                variant={activeTab === "home" ? "default" : "ghost"}
                onClick={() => setActiveTab("home")}
                className="nav-button"
              >
                <Calendar className="w-4 h-4 mr-2" />
                Home
              </Button>
              <Button
                variant={activeTab === "standings" ? "default" : "ghost"}
                onClick={() => setActiveTab("standings")}
                className="nav-button"
              >
                <Trophy className="w-4 h-4 mr-2" />
                Standings
              </Button>
            </div>
          )}
          
          <div className="nav-user">
            <Badge className="user-badge">
              {user.name} ({user.role})
            </Badge>
          </div>
        </nav>

        {/* Main Content */}
        <main className="main-content">
          {user.role === "League Manager" ? (
            <LeagueManagerDashboard />
          ) : (
            <PlayerDashboard />
          )}
        </main>
      </div>
    );
  };

  // Main App Logic
  if (currentView === "signup") {
    return <SignupView />;
  }

  return <DashboardView />;
}

export default App;