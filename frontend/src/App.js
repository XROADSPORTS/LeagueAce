import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { Calendar, Users, Trophy, Settings, Plus, TrendingUp, Clock, MapPin, UserCheck, Shield, Code, Copy, Eye, EyeOff, Bell, BellOff, Zap, Target, Camera, Upload, MessageCircle, Hash, Send, Paperclip, Smile } from "lucide-react";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Badge } from "./components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import { toast } from "./hooks/use-toast";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentView, setCurrentView] = useState("signup");
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("home");
  const [activeSport, setActiveSport] = useState("Tennis");
  const fileInputRef = useRef(null);
  
  // Data states
  const [leagues, setLeagues] = useState([]);
  const [seasons, setSeasons] = useState([]);
  const [formatTiers, setFormatTiers] = useState([]);
  const [ratingTiers, setRatingTiers] = useState([]);
  const [playerGroups, setPlayerGroups] = useState([]);
  const [userJoinedTiers, setUserJoinedTiers] = useState([]);
  const [userStandings, setUserStandings] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadManagerData = async () => {
    if (user && user.role === "League Manager") {
      try {
        const response = await axios.get(`${API}/users/${user.id}/leagues?sport_type=${activeSport}`);
        setLeagues(response.data);
      } catch (error) {
        console.error("Error loading manager data:", error);
      }
    }
  };

  const loadPlayerData = async () => {
    if (user && user.role === "Player") {
      try {
        const [joinedTiersRes, standingsRes] = await Promise.all([
          axios.get(`${API}/users/${user.id}/joined-tiers?sport_type=${activeSport}`),
          axios.get(`${API}/users/${user.id}/standings?sport_type=${activeSport}`)
        ]);
        setUserJoinedTiers(joinedTiersRes.data);
        setUserStandings(standingsRes.data);
      } catch (error) {
        console.error("Error loading player data:", error);
      }
    }
  };

  const loadNotifications = async () => {
    if (user) {
      try {
        const response = await axios.get(`${API}/users/${user.id}/notifications`);
        setNotifications(response.data);
      } catch (error) {
        console.error("Error loading notifications:", error);
      }
    }
  };

  useEffect(() => {
    if (user) {
      loadNotifications();
      if (user.role === "League Manager") {
        loadManagerData();
      } else if (user.role === "Player") {
        loadPlayerData();
      }
    }
  }, [user, activeSport]);

  // Profile Picture Upload
  const handleProfilePictureUpload = async (file) => {
    if (!file) return;
    
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      await axios.post(`${API}/users/${user.id}/upload-picture`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const updatedUser = await axios.get(`${API}/users/${user.id}`);
      setUser(updatedUser.data);
    } catch (error) {
      console.error("Error uploading profile picture:", error);
    }
    setLoading(false);
  };

  // Authentication functions (same as before)
  const handleGoogleSignIn = async () => {
    try {
      const mockGoogleResponse = {
        provider: "Google",
        token: "mock_google_token",
        email: "user@gmail.com",
        name: "Google User",
        provider_id: "google_123"
      };
      
      const response = await axios.post(`${API}/auth/social-login`, mockGoogleResponse);
      setUser(response.data);
      setCurrentView("sport-selection");
    } catch (error) {
      console.error("Error with Google sign-in:", error);
    }
  };

  const handleAppleSignIn = async () => {
    try {
      const mockAppleResponse = {
        provider: "Apple",
        token: "mock_apple_token",
        email: "user@icloud.com",
        name: "Apple User",
        provider_id: "apple_456"
      };
      
      const response = await axios.post(`${API}/auth/social-login`, mockAppleResponse);
      setUser(response.data);
      setCurrentView("sport-selection");
    } catch (error) {
      console.error("Error with Apple sign-in:", error);
    }
  };

  // Sport Selection Component (same as before)
  const SportSelection = () => {
    const [selectedSports, setSelectedSports] = useState([]);

    const handleSportSelection = async () => {
      if (selectedSports.length === 0) {
        alert("Please select at least one sport");
        return;
      }

      setLoading(true);
      try {
        await axios.patch(`${API}/users/${user.id}/sports`, {
          sports_preferences: selectedSports
        });
        
        const updatedUser = { ...user, sports_preferences: selectedSports };
        setUser(updatedUser);
        setCurrentView("dashboard");
        setActiveSport(selectedSports[0]);
      } catch (error) {
        console.error("Error updating sport preferences:", error);
      }
      setLoading(false);
    };

    const toggleSport = (sport) => {
      setSelectedSports(prev => 
        prev.includes(sport) 
          ? prev.filter(s => s !== sport)
          : [...prev, sport]
      );
    };

    return (
      <div className="sport-selection-container">
        <div className="leagueace-logo">
          <img 
            src="https://customer-assets.emergentagent.com/job_netly-sports/artifacts/92512jvn_AE260291-0518-44D4-AA45-1A273E36B765.png" 
            alt="LeagueAce" 
            className="logo-image"
          />
        </div>
        
        <div className="sport-selection-hero">
          <h1 className="sport-selection-title">
            Choose Your <span className="gradient-text-blue">Sports</span>
          </h1>
          <p className="sport-selection-subtitle">
            Select which sports you want to participate in. Tennis. Organized.
          </p>
        </div>
        
        <div className="sport-options">
          <Card 
            className={`glass-card-blue sport-option-card ${selectedSports.includes('Tennis') ? 'selected' : ''}`}
            onClick={() => toggleSport('Tennis')}
          >
            <CardContent className="sport-option-content">
              <Target className="sport-option-icon tennis-icon-blue" />
              <h3>Tennis Leagues</h3>
              <p>Join competitive tennis leagues with advanced organization</p>
              <ul className="sport-benefits">
                <li>Singles & Doubles formats</li>
                <li>4-Tier league structure</li>
                <li>Advanced Round Robin</li>
                <li>AI-powered grouping</li>
              </ul>
              {selectedSports.includes('Tennis') && (
                <Badge className="selected-badge-blue">Selected</Badge>
              )}
            </CardContent>
          </Card>

          <Card 
            className={`glass-card-blue sport-option-card ${selectedSports.includes('Pickleball') ? 'selected' : ''}`}
            onClick={() => toggleSport('Pickleball')}
          >
            <CardContent className="sport-option-content">
              <Zap className="sport-option-icon pickleball-icon-blue" />
              <h3>Pickleball Leagues</h3>
              <p>Fast-paced pickleball leagues for all skill levels</p>
              <ul className="sport-benefits">
                <li>Beginner-friendly format</li>
                <li>Social gameplay</li>
                <li>Mixed skill levels</li>
                <li>Community events</li>
              </ul>
              {selectedSports.includes('Pickleball') && (
                <Badge className="selected-badge-blue">Selected</Badge>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="sport-selection-actions">
          <Button 
            onClick={handleSportSelection}
            className="leagueace-button"
            disabled={selectedSports.length === 0 || loading}
          >
            {loading ? "Setting up..." : `Continue with ${selectedSports.length} sport${selectedSports.length !== 1 ? 's' : ''}`}
          </Button>
        </div>
      </div>
    );
  };

  // Signup Component (same as before with LeagueAce branding)
  const SignupView = () => {
    const [signupType, setSignupType] = useState(null);

    const SignupOptions = () => (
      <div className="signup-container">
        <div className="leagueace-logo">
          <img 
            src="https://customer-assets.emergentagent.com/job_netly-sports/artifacts/92512jvn_AE260291-0518-44D4-AA45-1A273E36B765.png" 
            alt="LeagueAce" 
            className="logo-image"
          />
        </div>
        
        <div className="signup-hero">
          <h1 className="signup-title">
            Welcome to <span className="gradient-text-blue">LeagueAce</span>
          </h1>
          <p className="signup-subtitle">
            Tennis. Organized. Choose how you want to participate.
          </p>
        </div>
        
        <div className="signup-options">
          <Card 
            className="glass-card-blue signup-option-card"
            onClick={() => setSignupType("player")}
          >
            <CardContent className="signup-option-content">
              <UserCheck className="signup-option-icon-blue" />
              <h3>Join as Player</h3>
              <p>Join leagues, play matches, and compete for rankings</p>
              <ul className="signup-benefits">
                <li>Join 4-tier league structure</li>
                <li>AI-powered group matching</li>
                <li>Integrated chat system</li>
                <li>Upload profile pictures</li>
              </ul>
            </CardContent>
          </Card>

          <Card 
            className="glass-card-blue signup-option-card"
            onClick={() => setSignupType("manager")}
          >
            <CardContent className="signup-option-content">
              <Shield className="signup-option-icon-blue" />
              <h3>Become League Manager</h3>
              <p>Create and manage comprehensive league structures</p>
              <ul className="signup-benefits">
                <li>4-tier league creation</li>
                <li>Advanced group management</li>
                <li>Chat moderation tools</li>
                <li>Full administrative control</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Social Login Options */}
        <div className="social-login-section">
          <div className="social-login-divider">
            <span>Or continue with</span>
          </div>
          <div className="social-login-buttons">
            <Button 
              onClick={handleGoogleSignIn}
              className="social-login-button google-button"
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" className="social-icon">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </Button>
            <Button 
              onClick={handleAppleSignIn}
              className="social-login-button apple-button"
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" className="social-icon">
                <path fill="currentColor" d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
              </svg>
              Continue with Apple
            </Button>
          </div>
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
          setCurrentView("sport-selection");
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
            className="back-button-blue"
          >
            ← Back to Options
          </Button>
          
          <Card className="glass-card-blue signup-form-card">
            <CardHeader>
              <CardTitle className="gradient-text-blue">
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
                    className="blue-input"
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
                    className="blue-input"
                  />
                </div>
                <div>
                  <Label htmlFor="phone">Phone Number (Optional)</Label>
                  <Input
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    placeholder="+1 (555) 123-4567"
                    className="blue-input"
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
                    className="blue-input"
                  />
                  <p className="rating-help-blue">
                    Rate yourself honestly: 3.0 = Beginner, 4.0 = Intermediate, 5.0+ = Advanced
                  </p>
                </div>
              </CardContent>
              <CardFooter>
                <Button type="submit" className="leagueace-button w-full" disabled={loading}>
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

  // Enhanced League Manager Dashboard with 4-Tier System
  const LeagueManagerDashboard = () => {
    const [activeManagerTab, setActiveManagerTab] = useState("overview");
    const [showCreateLeague, setShowCreateLeague] = useState(false);
    const [selectedLeague, setSelectedLeague] = useState(null);
    const [selectedSeason, setSelectedSeason] = useState(null);
    const [selectedFormatTier, setSelectedFormatTier] = useState(null);

    const CreateLeagueForm = () => {
      const [leagueData, setLeagueData] = useState({
        name: "",
        sport_type: activeSport,
        description: ""
      });

      const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
          await axios.post(`${API}/leagues?created_by=${user.id}`, leagueData);
          loadManagerData();
          setShowCreateLeague(false);
          setLeagueData({ name: "", sport_type: activeSport, description: "" });
        } catch (error) {
          console.error("Error creating league:", error);
        }
        setLoading(false);
      };

      return (
        <Card className="glass-card-blue">
          <CardHeader>
            <CardTitle>Create New {activeSport} League</CardTitle>
            <CardDescription>Set up a new league with 4-tier structure</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="league-name">League Name</Label>
                <Input
                  id="league-name"
                  value={leagueData.name}
                  onChange={(e) => setLeagueData({...leagueData, name: e.target.value})}
                  placeholder={`e.g., Central Park ${activeSport} League`}
                  required
                  className="blue-input"
                />
              </div>
              <div>
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  value={leagueData.description}
                  onChange={(e) => setLeagueData({...leagueData, description: e.target.value})}
                  placeholder={`Describe this ${activeSport} league...`}
                  className="blue-textarea"
                />
              </div>
            </CardContent>
            <CardFooter className="space-x-2">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setShowCreateLeague(false)}
                className="blue-outline-button"
              >
                Cancel
              </Button>
              <Button type="submit" className="leagueace-button" disabled={loading}>
                {loading ? "Creating..." : `Create ${activeSport} League`}
              </Button>
            </CardFooter>
          </form>
        </Card>
      );
    };

    const FourTierManagement = () => {
      const [seasons, setSeasons] = useState([]);

      const loadSeasons = async (leagueId) => {
        try {
          const response = await axios.get(`${API}/leagues/${leagueId}/seasons`);
          setSeasons(response.data);
        } catch (error) {
          console.error("Error loading seasons:", error);
        }
      };

      const loadFormatTiers = async (seasonId) => {
        try {
          const response = await axios.get(`${API}/seasons/${seasonId}/format-tiers`);
          setFormatTiers(response.data);
        } catch (error) {
          console.error("Error loading format tiers:", error);
        }
      };

      const loadRatingTiers = async (formatTierId) => {
        try {
          const response = await axios.get(`${API}/format-tiers/${formatTierId}/rating-tiers`);
          setRatingTiers(response.data);
        } catch (error) {
          console.error("Error loading rating tiers:", error);
        }
      };

      const createSeason = async (leagueId, seasonName) => {
        try {
          const seasonData = {
            league_id: leagueId,
            name: seasonName,
            start_date: new Date().toISOString().split('T')[0],
            end_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
          };
          await axios.post(`${API}/seasons`, seasonData);
          loadSeasons(leagueId);
        } catch (error) {
          console.error("Error creating season:", error);
        }
      };

      const createFormatTier = async (seasonId, formatData) => {
        try {
          await axios.post(`${API}/format-tiers`, {
            season_id: seasonId,
            ...formatData
          });
          loadFormatTiers(seasonId);
        } catch (error) {
          console.error("Error creating format tier:", error);
        }
      };

      const createRatingTier = async (formatTierId, ratingData) => {
        try {
          await axios.post(`${API}/rating-tiers`, {
            format_tier_id: formatTierId,
            ...ratingData
          });
          loadRatingTiers(formatTierId);
        } catch (error) {
          console.error("Error creating rating tier:", error);
        }
      };

      return (
        <div className="four-tier-management">
          {/* Tier 1: League Selection */}
          <div className="tier-section">
            <h3 className="tier-title">Tier 1: Leagues</h3>
            <div className="leagues-grid">
              {leagues.map((league) => (
                <Card 
                  key={league.id} 
                  className={`glass-card-blue league-card ${selectedLeague?.id === league.id ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedLeague(league);
                    loadSeasons(league.id);
                    setSelectedSeason(null);
                    setSelectedFormatTier(null);
                  }}
                >
                  <CardHeader>
                    <CardTitle>{league.name}</CardTitle>
                    <CardDescription>{league.sport_type} League</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Badge className="sport-type-badge-blue">{league.sport_type}</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Tier 2: Season Management */}
          {selectedLeague && (
            <div className="tier-section">
              <h3 className="tier-title">Tier 2: Seasons for {selectedLeague.name}</h3>
              <div className="season-controls">
                <Button 
                  className="leagueace-button"
                  onClick={() => {
                    const seasonName = prompt("Enter season name:");
                    if (seasonName) createSeason(selectedLeague.id, seasonName);
                  }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Season
                </Button>
              </div>
              <div className="seasons-grid">
                {seasons.map((season) => (
                  <Card 
                    key={season.id} 
                    className={`glass-card-blue season-card ${selectedSeason?.id === season.id ? 'selected' : ''}`}
                    onClick={() => {
                      setSelectedSeason(season);
                      loadFormatTiers(season.id);
                      setSelectedFormatTier(null);
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
                      <Badge className="sport-badge-blue">{season.status}</Badge>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Tier 3: Format Tiers (Singles, Doubles, Round Robin) */}
          {selectedSeason && (
            <div className="tier-section">
              <h3 className="tier-title">Tier 3: Formats for {selectedSeason.name}</h3>
              <div className="format-controls">
                <Button 
                  className="leagueace-button"
                  onClick={() => createFormatTier(selectedSeason.id, {
                    name: "Singles",
                    format_type: "Singles",
                    description: "Singles format matches"
                  })}
                >
                  Add Singles
                </Button>
                <Button 
                  className="leagueace-button"
                  onClick={() => createFormatTier(selectedSeason.id, {
                    name: "Doubles",
                    format_type: "Doubles",
                    description: "Doubles format matches"
                  })}
                >
                  Add Doubles
                </Button>
                <Button 
                  className="leagueace-button"
                  onClick={() => createFormatTier(selectedSeason.id, {
                    name: "Round Robin",
                    format_type: "Doubles",
                    description: "Advanced Round Robin format"
                  })}
                >
                  Add Round Robin
                </Button>
              </div>
              <div className="format-tiers-grid">
                {formatTiers.map((tier) => (
                  <Card 
                    key={tier.id} 
                    className={`glass-card-blue format-tier-card ${selectedFormatTier?.id === tier.id ? 'selected' : ''}`}
                    onClick={() => {
                      setSelectedFormatTier(tier);
                      loadRatingTiers(tier.id);
                    }}
                  >
                    <CardHeader>
                      <CardTitle>{tier.name}</CardTitle>
                      <CardDescription>{tier.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Badge className="format-badge">{tier.format_type}</Badge>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Tier 4: Rating Tiers (4.0, 4.5, 5.0) */}
          {selectedFormatTier && (
            <div className="tier-section">
              <h3 className="tier-title">Tier 4: Rating Levels for {selectedFormatTier.name}</h3>
              <div className="rating-controls">
                <RatingTierCreator 
                  formatTierId={selectedFormatTier.id}
                  onRatingTierCreated={() => loadRatingTiers(selectedFormatTier.id)}
                />
              </div>
              <div className="rating-tiers-grid">
                {ratingTiers.map((tier) => (
                  <RatingTierCard key={tier.id} tier={tier} />
                ))}
              </div>
            </div>
          )}
        </div>
      );
    };

    const RatingTierCreator = ({ formatTierId, onRatingTierCreated }) => {
      const [showForm, setShowForm] = useState(false);
      const [tierData, setTierData] = useState({
        name: "",
        min_rating: 3.0,
        max_rating: 3.5,
        max_players: 36,
        competition_system: "Team League Format",
        playoff_spots: 8,
        region: "General",
        surface: "Hard Court"
      });

      const handleSubmit = async (e) => {
        e.preventDefault();
        try {
          await axios.post(`${API}/rating-tiers`, {
            format_tier_id: formatTierId,
            ...tierData
          });
          onRatingTierCreated();
          setShowForm(false);
          setTierData({
            name: "",
            min_rating: 3.0,
            max_rating: 3.5,
            max_players: 36,
            competition_system: "Team League Format",
            playoff_spots: 8,
            region: "General",
            surface: "Hard Court"
          });
        } catch (error) {
          console.error("Error creating rating tier:", error);
        }
      };

      if (!showForm) {
        return (
          <Button 
            className="leagueace-button"
            onClick={() => setShowForm(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Rating Tier
          </Button>
        );
      }

      return (
        <Card className="glass-card-blue rating-tier-form">
          <CardHeader>
            <CardTitle>Create Rating Tier</CardTitle>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div className="form-row">
                <div>
                  <Label>Tier Name</Label>
                  <Input
                    value={tierData.name}
                    onChange={(e) => setTierData({...tierData, name: e.target.value})}
                    placeholder="e.g., 4.0, 4.5, 5.0"
                    required
                    className="blue-input"
                  />
                </div>
                <div>
                  <Label>Min Rating</Label>
                  <Input
                    type="number"
                    min="3.0"
                    max="5.5"
                    step="0.1"
                    value={tierData.min_rating}
                    onChange={(e) => setTierData({...tierData, min_rating: parseFloat(e.target.value)})}
                    required
                    className="blue-input"
                  />
                </div>
                <div>
                  <Label>Max Rating</Label>
                  <Input
                    type="number"
                    min="3.0"
                    max="5.5"
                    step="0.1"
                    value={tierData.max_rating}
                    onChange={(e) => setTierData({...tierData, max_rating: parseFloat(e.target.value)})}
                    required
                    className="blue-input"
                  />
                </div>
              </div>
              <div className="form-row">
                <div>
                  <Label>Max Players</Label>
                  <Input
                    type="number"
                    min="8"
                    max="100"
                    value={tierData.max_players}
                    onChange={(e) => setTierData({...tierData, max_players: parseInt(e.target.value)})}
                    required
                    className="blue-input"
                  />
                </div>
                <div>
                  <Label>Competition System</Label>
                  <Select 
                    value={tierData.competition_system} 
                    onValueChange={(value) => setTierData({...tierData, competition_system: value})}
                  >
                    <SelectTrigger className="blue-input">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Team League Format">Team League Format</SelectItem>
                      <SelectItem value="Knockout System">Knockout System</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {tierData.competition_system === "Team League Format" && (
                  <div>
                    <Label>Playoff Spots</Label>
                    <Input
                      type="number"
                      min="4"
                      max="16"
                      value={tierData.playoff_spots}
                      onChange={(e) => setTierData({...tierData, playoff_spots: parseInt(e.target.value)})}
                      className="blue-input"
                    />
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter className="space-x-2">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setShowForm(false)}
                className="blue-outline-button"
              >
                Cancel
              </Button>
              <Button type="submit" className="leagueace-button">
                Create Tier
              </Button>
            </CardFooter>
          </form>
        </Card>
      );
    };

    const RatingTierCard = ({ tier }) => {
      const [groups, setGroups] = useState([]);
      const [showGroupForm, setShowGroupForm] = useState(false);

      const loadGroups = async () => {
        try {
          const response = await axios.get(`${API}/rating-tiers/${tier.id}/groups`);
          setGroups(response.data);
        } catch (error) {
          console.error("Error loading groups:", error);
        }
      };

      useEffect(() => {
        loadGroups();
      }, [tier.id]);

      const createGroups = async (groupSize, customNames) => {
        try {
          await axios.post(`${API}/rating-tiers/${tier.id}/create-groups`, {
            group_size: groupSize,
            custom_names: customNames
          });
          loadGroups();
          setShowGroupForm(false);
        } catch (error) {
          console.error("Error creating groups:", error);
        }
      };

      return (
        <Card className="glass-card-blue rating-tier-card">
          <CardHeader>
            <CardTitle>{tier.name}</CardTitle>
            <CardDescription>
              Rating: {tier.min_rating} - {tier.max_rating} | {tier.max_players} max players
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="tier-details">
              <div className="join-code-display">
                <Code className="w-4 h-4" />
                <span>{tier.join_code}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => navigator.clipboard?.writeText(tier.join_code)}
                >
                  <Copy className="w-3 h-3" />
                </Button>
              </div>
              
              <div className="competition-info">
                <Badge className="competition-badge">{tier.competition_system}</Badge>
                {tier.playoff_spots && (
                  <Badge variant="outline">Top {tier.playoff_spots} to Playoffs</Badge>
                )}
              </div>

              <div className="groups-section">
                <h4>Player Groups ({groups.length})</h4>
                {groups.length > 0 ? (
                  <div className="groups-list">
                    {groups.map((group) => (
                      <div key={group.id} className="group-item">
                        <Badge className="group-badge">
                          {group.name}
                        </Badge>
                        <GroupManagement groupId={group.id} tierId={tier.id} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="no-groups">No groups created yet</p>
                )}
                
                {!showGroupForm ? (
                  <Button 
                    className="leagueace-button mt-2"
                    onClick={() => setShowGroupForm(true)}
                  >
                    Create Groups
                  </Button>
                ) : (
                  <GroupCreatorForm 
                    onCreateGroups={createGroups}
                    onCancel={() => setShowGroupForm(false)}
                  />
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      );
    };

    const GroupCreatorForm = ({ onCreateGroups, onCancel }) => {
      const [groupSize, setGroupSize] = useState(12);
      const [customNames, setCustomNames] = useState("");

      const handleSubmit = (e) => {
        e.preventDefault();
        const names = customNames.trim() ? customNames.split(',').map(name => name.trim()) : null;
        onCreateGroups(groupSize, names);
      };

      return (
        <form onSubmit={handleSubmit} className="group-creator-form">
          <div className="form-row">
            <div>
              <Label>Group Size</Label>
              <Input
                type="number"
                min="8"
                max="20"
                value={groupSize}
                onChange={(e) => setGroupSize(parseInt(e.target.value))}
                className="blue-input"
              />
            </div>
          </div>
          <div>
            <Label>Custom Group Names (Optional)</Label>
            <Input
              value={customNames}
              onChange={(e) => setCustomNames(e.target.value)}
              placeholder="Group Alpha, Group Beta, Group Gamma"
              className="blue-input"
            />
            <p className="help-text">Leave empty for Group A, B, C...</p>
          </div>
          <div className="form-actions">
            <Button type="button" variant="outline" onClick={onCancel} className="blue-outline-button">
              Cancel
            </Button>
            <Button type="submit" className="leagueace-button">
              Create Groups
            </Button>
          </div>
        </form>
      );
    };

    const GroupManagement = ({ groupId, tierId }) => {
      const [schedule, setSchedule] = useState(null);
      const [matches, setMatches] = useState([]);
      const [selectedWeek, setSelectedWeek] = useState(1);
      const [loading, setLoading] = useState(false);

      const loadSchedule = async () => {
        try {
          const response = await axios.get(`${API}/player-groups/${groupId}/schedule`);
          setSchedule(response.data);
        } catch (error) {
          // Schedule doesn't exist yet
          setSchedule(null);
        }
      };

      const loadMatches = async (week = selectedWeek) => {
        try {
          const response = await axios.get(`${API}/player-groups/${groupId}/matches?week_number=${week}`);
          setMatches(response.data);
        } catch (error) {
          console.error("Error loading matches:", error);
        }
      };

      useEffect(() => {
        loadSchedule();
        loadMatches();
      }, [groupId, selectedWeek]);

      const generateSchedule = async () => {
        setLoading(true);
        try {
          await axios.post(`${API}/player-groups/${groupId}/generate-schedule`);
          await loadSchedule();
          toast({ title: "Success", description: "Round robin schedule generated!" });
        } catch (error) {
          toast({ title: "Error", description: error.response?.data?.detail || "Failed to generate schedule", variant: "destructive" });
        }
        setLoading(false);
      };

      const createWeekMatches = async () => {
        setLoading(true);
        try {
          await axios.post(`${API}/player-groups/${groupId}/create-matches`, {
            player_group_id: groupId,
            week_number: selectedWeek
          });
          await loadMatches();
          toast({ title: "Success", description: `Week ${selectedWeek} matches created!` });
        } catch (error) {
          toast({ title: "Error", description: error.response?.data?.detail || "Failed to create matches", variant: "destructive" });
        }
        setLoading(false);
      };

      return (
        <div className="group-management">
          {!schedule ? (
            <Button 
              size="sm" 
              className="leagueace-button"
              onClick={generateSchedule}
              disabled={loading}
            >
              {loading ? "Generating..." : "Generate Round Robin Schedule"}
            </Button>
          ) : (
            <div className="schedule-management">
              <div className="schedule-info">
                <Badge variant="outline">
                  {schedule.total_weeks} weeks, {schedule.matches_per_week} matches/week
                </Badge>
              </div>
              
              <div className="week-controls">
                <Select value={selectedWeek.toString()} onValueChange={(value) => setSelectedWeek(parseInt(value))}>
                  <SelectTrigger className="blue-input w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[...Array(schedule.total_weeks)].map((_, i) => (
                      <SelectItem key={i + 1} value={(i + 1).toString()}>
                        Week {i + 1}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                <Button 
                  size="sm" 
                  className="leagueace-button"
                  onClick={createWeekMatches}
                  disabled={loading || matches.length > 0}
                >
                  {loading ? "Creating..." : `Create Week ${selectedWeek} Matches`}
                </Button>
              </div>

              {matches.length > 0 && (
                <div className="matches-list">
                  <h5>Week {selectedWeek} Matches ({matches.length})</h5>
                  {matches.map((match) => (
                    <Badge key={match.id} className="match-badge" variant="outline">
                      {match.format} - {match.status}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      );
    };

    return (
      <div className="manager-dashboard">
        <div className="dashboard-header">
          <h2 className="section-title-blue">{activeSport} League Manager Dashboard</h2>
          <div className="manager-stats">
            <Badge className="stat-badge-blue">
              {leagues.length} {activeSport} Leagues Created
            </Badge>
          </div>
        </div>

        <Tabs value={activeManagerTab} onValueChange={setActiveManagerTab}>
          <TabsList className="manager-tabs-blue">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="four-tier">4-Tier Management</TabsTrigger>
            <TabsTrigger value="chat">League Chat</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="manager-overview">
              {!showCreateLeague ? (
                <Card className="glass-card-blue">
                  <CardContent className="create-season-prompt">
                    <Trophy className="prompt-icon-blue" />
                    <h3>Ready to Create Your {activeSport} League?</h3>
                    <p>Build comprehensive {activeSport} leagues with 4-tier structure. Tennis. Organized.</p>
                    <Button 
                      className="leagueace-button"
                      onClick={() => setShowCreateLeague(true)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create New {activeSport} League
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <CreateLeagueForm />
              )}
            </div>
          </TabsContent>

          <TabsContent value="four-tier">
            <FourTierManagement />
          </TabsContent>

          <TabsContent value="chat">
            <div className="chat-management">
              <h3>Chat Management</h3>
              <p>League chat features coming soon...</p>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    );
  };

  // Continue with Player Dashboard and other components...
  // (Player Dashboard, Navigation, etc. remain similar but updated for new structure)

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

    return (
      <div className="player-dashboard">
        <Card className="glass-card-blue">
          <CardHeader>
            <CardTitle>Join a {activeSport} League</CardTitle>
            <CardDescription>
              Enter a 6-character join code to join a specific rating tier
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!showJoinForm ? (
              <Button 
                className="leagueace-button"
                onClick={() => setShowJoinForm(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                Join New {activeSport} League
              </Button>
            ) : (
              <form onSubmit={handleJoinByCode} className="join-form">
                <div className="join-input-group">
                  <Input
                    value={joinCode}
                    onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                    placeholder="Enter 6-character join code"
                    maxLength={6}
                    className="join-code-input-blue"
                    required
                  />
                  <Button type="submit" className="leagueace-button" disabled={loading}>
                    {loading ? "Joining..." : "Join"}
                  </Button>
                </div>
                <Button 
                  type="button" 
                  variant="ghost" 
                  onClick={() => setShowJoinForm(false)}
                  className="cancel-join-blue"
                >
                  Cancel
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    );
  };

  // Main Dashboard Component
  const DashboardView = () => {
    if (!user) return null;

    const unreadNotifications = notifications.filter(n => !n.read).length;

    return (
      <div className="app-container-blue">
        <nav className="nav-glass-blue">
          <div className="nav-brand">
            <h1 className="nav-logo-blue">LeagueAce</h1>
            <span className="nav-tagline">Tennis. Organized.</span>
          </div>

          {user.sports_preferences && user.sports_preferences.length > 1 && (
            <div className="sport-switcher">
              <Tabs value={activeSport} onValueChange={setActiveSport}>
                <TabsList className="sport-tabs-blue">
                  {user.sports_preferences.map(sport => (
                    <TabsTrigger key={sport} value={sport} className="sport-tab-blue">
                      {sport === "Tennis" ? <Target className="w-4 h-4 mr-1" /> : <Zap className="w-4 h-4 mr-1" />}
                      {sport}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
            </div>
          )}
          
          {user.role === "League Manager" ? (
            <div className="nav-tabs">
              <Button
                variant={activeTab === "home" ? "default" : "ghost"}
                onClick={() => setActiveTab("home")}
                className="nav-button-blue"
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
                className="nav-button-blue"
              >
                <Calendar className="w-4 h-4 mr-2" />
                Home
              </Button>
            </div>
          )}
          
          <div className="nav-user">
            <div className="notification-bell-blue">
              <Bell className="w-5 h-5" />
              {unreadNotifications > 0 && (
                <Badge className="notification-badge-blue">{unreadNotifications}</Badge>
              )}
            </div>
            <div className="nav-user-info">
              {user.profile_picture && (
                <img src={user.profile_picture} alt="Profile" className="nav-profile-picture" />
              )}
              <Badge className="user-badge-blue">
                {user.name} ({user.role})
              </Badge>
            </div>
          </div>
        </nav>

        <main className="main-content-blue">
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

  if (currentView === "sport-selection") {
    return <SportSelection />;
  }

  return <DashboardView />;
}

export default App;