import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { Calendar, Users, Trophy, Settings, Plus, TrendingUp, Clock, MapPin, UserCheck, Shield, Code, Copy, Eye, EyeOff, Bell, BellOff, Zap, Target, Camera, Upload, MessageCircle, Hash, Send, Paperclip, Smile, CheckCircle, Shuffle } from "lucide-react";
import QRCode from "react-qr-code";
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

// Capture ?join=CODE from URL and stash for later (player flow)
const getPendingJoinCodeFromURL = () => {
  try {
    const url = new URL(window.location.href);
    const raw = url.searchParams.get('join');
    if (!raw) return null;
    const code = (raw || '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (code.length === 6) return code;
  } catch (_) {}
  return null;
};

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
            src="https://customer-assets.emergentagent.com/job_courtmaster-1/artifacts/kde0l6pr_leagueAce%20combo%20logo%20with%20slogans.png" 
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
              <Target className="sport-option-icon tennis-icon-blue glass-icon" />
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
              <Zap className="sport-option-icon pickleball-icon-blue glass-icon" />
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
            className="btn-primary-ios"
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
            src="https://customer-assets.emergentagent.com/job_courtmaster-1/artifacts/kde0l6pr_leagueAce%20combo%20logo%20with%20slogans.png" 
            alt="LeagueAce" 
            className="logo-image"
          />
        </div>
        
        <div className="signup-hero">
          <h1 className="signup-title">
            <span className="gradient-text-blue">Find Your Match</span>
          </h1>
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
                <Button type="submit" className="btn-primary-ios w-full" disabled={loading}>
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
              <Button type="submit" className="btn-primary-ios" disabled={loading}>
                {loading ? "Creating..." : `Create ${activeSport} League`}
              </Button>
            </CardFooter>
          </form>
        </Card>
      );
    };

    const SeasonCreator = ({ leagueId, onSeasonCreated }) => {
      const [showForm, setShowForm] = useState(false);
      const [loading, setLoading] = useState(false);
      const [seasonData, setSeasonData] = useState({
        name: "",
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      });

      const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
          await axios.post(`${API}/seasons`, {
            league_id: leagueId,
            ...seasonData
          });
          
          toast({ 
            title: "Success", 
            description: `Season "${seasonData.name}" created successfully!` 
          });
          
          onSeasonCreated();
          setShowForm(false);
          setSeasonData({
            name: "",
            start_date: new Date().toISOString().split('T')[0],
            end_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
          });
        } catch (error) {
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to create season",
            variant: "destructive"
          });
        }
        setLoading(false);
      };

      if (!showForm) {
        return (
          <Button 
            className="btn-primary-ios"
            onClick={() => setShowForm(true)}
          >
            <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
            Add Season
          </Button>
        );
      }

      return (
        <Card className="glass-card-blue season-creator-form">
          <CardHeader>
            <CardTitle>Create New Season</CardTitle>
            <CardDescription>Add a new season to your league</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="season-form">
              <div className="form-group">
                <Label htmlFor="season-name">Season Name</Label>
                <Input
                  id="season-name"
                  type="text"
                  placeholder="e.g., Spring 2024, Fall Tournament"
                  value={seasonData.name}
                  onChange={(e) => setSeasonData({...seasonData, name: e.target.value})}
                  className="blue-input"
                  required
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <Label htmlFor="start-date">Start Date</Label>
                  <Input
                    id="start-date"
                    type="date"
                    value={seasonData.start_date}
                    onChange={(e) => setSeasonData({...seasonData, start_date: e.target.value})}
                    className="blue-input"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <Label htmlFor="end-date">End Date</Label>
                  <Input
                    id="end-date"
                    type="date"
                    value={seasonData.end_date}
                    onChange={(e) => setSeasonData({...seasonData, end_date: e.target.value})}
                    className="blue-input"
                    required
                  />
                </div>
              </div>
              
              <div className="form-actions">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setShowForm(false)}
                  className="blue-outline-button"
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  className="btn-primary-ios"
                  disabled={loading || !seasonData.name.trim()}
                >
                  {loading ? "Creating..." : "Create Season"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      );
    };


    const JoinRequestsPanel = () => {
      const [items, setItems] = useState([]);
      const [loadingReq, setLoadingReq] = useState(false);

      const load = async () => {
        if (!user || user.role !== "League Manager") return;
        setLoadingReq(true);
        try {
          const { data } = await axios.get(`${API}/join-requests`, { params: { manager_id: user.id } });
          setItems(data?.requests || []);
        } catch (err) {
          console.error('Error loading join requests', err);
        }
        setLoadingReq(false);
      };

      useEffect(() => { load(); }, [user?.id]);

      const approve = async (id) => {
        try {
          await axios.post(`${API}/join-requests/${id}/approve`);
          toast({ title: 'Approved', description: 'Player added and tier range updated if needed' });
          load();
        } catch (err) {
          toast({ title: 'Error', description: err.response?.data?.detail || 'Failed to approve', variant: 'destructive' });
        }
      };

      const reject = async (id) => {
        try {
          await axios.post(`${API}/join-requests/${id}/reject`);
          toast({ title: 'Rejected', description: 'Request rejected' });
          load();
        } catch (err) {
          toast({ title: 'Error', description: err.response?.data?.detail || 'Failed to reject', variant: 'destructive' });
        }
      };

      if (!user || user.role !== 'League Manager') return null;

      return (
        <div className="join-requests">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <p style={{ opacity: 0.85 }}>{items.length} pending</p>
            <Button variant="outline" className="blue-outline-button" onClick={load} disabled={loadingReq}>{loadingReq ? 'Refreshing…' : 'Refresh'}</Button>
          </div>
          {items.length === 0 ? (
            <div className="empty-state">No pending join requests.</div>
          ) : (
            <div className="requests-list" style={{ display: 'grid', gap: 12 }}>
              {items.map((r) => (
                <div key={r.id} className="request-item glass-layer-1" style={{ padding: 12, borderRadius: 12 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8, alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{r.user_name || r.user_email}</div>
                      <div style={{ fontSize: 13, opacity: 0.8 }}>{r.user_email} • Rating {r.user_rating ?? 'n/a'}</div>
                      <div style={{ fontSize: 13, opacity: 0.8 }}>{r.league_name} • {r.rating_tier_name} • Code {r.join_code}</div>
                      {r.message && (<div style={{ fontSize: 13, opacity: 0.9, marginTop: 4 }}>“{r.message}”</div>)}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <Button className="btn-primary-ios" onClick={() => approve(r.id)}>Approve</Button>
                      <Button variant="outline" className="blue-outline-button" onClick={() => reject(r.id)}>Reject</Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    };

    const FourTierManagement = () => {
      const [formatTiers, setFormatTiers] = useState([]);
      const [ratingTiers, setRatingTiers] = useState([]);

      const loadFormatTiers = async (leagueId) => {
        try {
          // Modified to load format tiers directly from league
          const response = await axios.get(`${API}/leagues/${leagueId}/format-tiers`);
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

      const createFormatTier = async (leagueId, formatData) => {
        try {
          // Modified to create format tier directly under league
          await axios.post(`${API}/format-tiers`, {
            league_id: leagueId,  // Changed from season_id to league_id
            ...formatData
          });
          loadFormatTiers(leagueId);
          toast({ 
            title: "Success", 
            description: `${formatData.name} format created successfully!` 
          });
        } catch (error) {
          console.error("Error creating format tier:", error);
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to create format tier",
            variant: "destructive"
          });
        }
      };

      const createRatingTier = async (formatTierId, ratingData) => {
        try {
          await axios.post(`${API}/rating-tiers`, {
            format_tier_id: formatTierId,
            ...ratingData
          });
          loadRatingTiers(formatTierId);
          toast({ 
            title: "Success", 
            description: `Rating tier "${ratingData.name}" created with join code!` 
          });
        } catch (error) {
          console.error("Error creating rating tier:", error);
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to create rating tier",
            variant: "destructive"
          });
        }
      };

      return (
        <div className="four-tier-management">
          <div className="tier-instructions">
            <Card className="glass-card-blue instruction-card">
              <CardContent className="instruction-content">
                <h4>🎾 League Creation Structure</h4>
                <ol className="setup-steps">
                  <li><strong>Tier 1:</strong> Select your League</li>
                  <li><strong>Tier 2:</strong> Add Formats (Singles, Doubles, Round Robin)</li>
                  <li><strong>Tier 3:</strong> Create Rating Tiers (4.0, 4.5, 5.0) - Each gets unique join code</li>
                  <li><strong>Tier 4:</strong> System auto-creates player groups (Group A, B, C) when needed</li>
                </ol>
                <div className="key-features">
                  <Badge className="feature-badge">✅ Unique Join Codes</Badge>
                  <Badge className="feature-badge">✅ Auto Player Groups</Badge>
                  <Badge className="feature-badge">✅ Competition Systems</Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tier 1: League Selection */}
          <div className="tier-section">
            <h3 className="tier-title">Tier 1: Select League to Configure</h3>
            <div className="leagues-grid">
              {leagues.length === 0 ? (
                <Card className="glass-card-blue empty-state-card">
                  <CardContent className="empty-state">
                    <div className="empty-icon">🏆</div>
                    <h4>No leagues yet</h4>
                    <p>Create your first league to get started. It will persist and appear here after refresh.</p>
                  </CardContent>
                </Card>
              ) : leagues.map((league) => (
                <Card 
                  key={league.id} 
                  className={`glass-card-blue league-card ${selectedLeague?.id === league.id ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedLeague(league);
                    loadFormatTiers(league.id);
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

          {/* Tier 2: Format Types (Singles, Doubles, Round Robin) */}
          {selectedLeague && (
            <div className="tier-section">
              <h3 className="tier-title">Tier 2: Add Formats for {selectedLeague.name}</h3>
              <div className="format-controls">
                <Button 
                  className="btn-primary-ios"
                  onClick={() => createFormatTier(selectedLeague.id, {
                    name: "Singles",
                    format_type: "Singles",
                    description: "Singles format matches - individual competition"
                  })}
                >
                  <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
                  Add Singles
                </Button>
                <Button 
                  className="btn-primary-ios"
                  onClick={() => createFormatTier(selectedLeague.id, {
                    name: "Doubles",
                    format_type: "Doubles",
                    description: "Doubles format matches - team competition"
                  })}
                >
                  <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
                  Add Doubles
                </Button>
                <Button 
                  className="btn-primary-ios"
                  onClick={() => createFormatTier(selectedLeague.id, {
                    name: "Round Robin Doubles",
                    format_type: "Doubles",
                    description: "Round Robin format - partners rotate automatically"
                  })}
                >
                  <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
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
                {formatTiers.length === 0 && (
                  <div className="empty-state">
                    <p>No format types created yet. Click "Add Singles", "Add Doubles", or "Add Round Robin" to create tournament formats!</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tier 3: Rating Tiers (4.0, 4.5, 5.0) with Join Codes */}
          {selectedFormatTier && (
            <div className="tier-section">
              <h3 className="tier-title">Tier 3: Create Rating Levels for {selectedFormatTier.name}</h3>
              <div className="rating-info">
                <Card className="glass-card-blue info-card">
                  <CardContent>
                    <p>Each rating tier will get a <strong>unique 6-character join code</strong> that players use to join. 
                    You can create as many rating levels as needed (4.0, 4.5, 5.0, etc.).</p>
                  </CardContent>
                </Card>
              </div>
              <div className="rating-controls">
                <EnhancedRatingTierCreator 
                  formatTierId={selectedFormatTier.id}
                  onRatingTierCreated={() => loadRatingTiers(selectedFormatTier.id)}
                />
              </div>
              <div className="rating-tiers-grid">
                {ratingTiers.map((tier) => (
                  <EnhancedRatingTierCard key={tier.id} tier={tier} />
                ))}
                {ratingTiers.length === 0 && (
                  <div className="empty-state">
                    <p>No rating tiers created yet. Click "Add Rating Tier" to create skill-based divisions like 4.0, 4.5, 5.0!</p>
                  </div>
                )}
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
            className="btn-primary-ios"
            onClick={() => setShowForm(true)}
          >
            <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
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
              <Button type="submit" className="btn-primary-ios">
                Create Tier
              </Button>
            </CardFooter>
          </form>
        </Card>
      );
    };
    const EnhancedRatingTierCreator = ({ formatTierId, onRatingTierCreated }) => {
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
          const response = await axios.post(`${API}/rating-tiers`, {
            format_tier_id: formatTierId,
            ...tierData
          });
          
          // Show the join code in the success message
          const joinCode = response.data?.join_code || 'Generated';
          toast({ 
            title: "Rating Tier Created!", 
            description: `"${tierData.name}" created successfully! Join Code: ${joinCode}` 
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
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to create rating tier",
            variant: "destructive"
          });
        }
      };

      if (!showForm) {
        return (
          <Button 
            className="btn-primary-ios"
            onClick={() => setShowForm(true)}
          >
            <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
            Add Rating Tier (4.0, 4.5, 5.0, etc.)
          </Button>
        );
      }

      return (
        <Card className="glass-card-blue rating-creator-form">
          <CardHeader>
            <CardTitle>Create New Rating Tier</CardTitle>
            <CardDescription>Define skill level and competition settings - unique join code will be generated</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="rating-form">
              <div className="form-row">
                <div className="form-group">
                  <Label htmlFor="tier-name">Tier Name (e.g., 4.0, 4.5, 5.0)</Label>
                  <Input
                    id="tier-name"
                    type="text"
                    placeholder="4.0, 4.5, 5.0, Beginner, Advanced"
                    value={tierData.name}
                    onChange={(e) => setTierData({...tierData, name: e.target.value})}
                    className="blue-input"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <Label htmlFor="max-players">Max Players (Optional)</Label>
                  <Input
                    id="max-players"
                    type="number"
                    min="4"
                    max="100"
                    value={tierData.max_players}
                    onChange={(e) => setTierData({...tierData, max_players: parseInt(e.target.value)})}
                    className="blue-input"
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <Label htmlFor="min-rating">Minimum Rating</Label>
                  <Input
                    id="min-rating"
                    type="number"
                    step="0.1"
                    min="3.0"
                    max="5.5"
                    value={tierData.min_rating}
                    onChange={(e) => setTierData({...tierData, min_rating: parseFloat(e.target.value)})}
                    className="blue-input"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <Label htmlFor="max-rating">Maximum Rating</Label>
                  <Input
                    id="max-rating"
                    type="number"
                    step="0.1"
                    min="3.0"
                    max="5.5"
                    value={tierData.max_rating}
                    onChange={(e) => setTierData({...tierData, max_rating: parseFloat(e.target.value)})}
                    className="blue-input"
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <Label htmlFor="competition-system">Competition System</Label>
                <Select 
                  value={tierData.competition_system} 
                  onValueChange={(value) => setTierData({...tierData, competition_system: value})}
                >
                  <SelectTrigger className="blue-input">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Team League Format">🏆 Team League Format</SelectItem>
                    <SelectItem value="Knockout System">⚡ Knockout System</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {tierData.competition_system === "Team League Format" && (
                <div className="form-group">
                  <Label htmlFor="playoff-spots">Playoff Spots (Top players advance)</Label>
                  <Select 
                    value={tierData.playoff_spots.toString()} 
                    onValueChange={(value) => setTierData({...tierData, playoff_spots: parseInt(value)})}
                  >
                    <SelectTrigger className="blue-input">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="4">Top 4 players</SelectItem>
                      <SelectItem value="8">Top 8 players</SelectItem>
                      <SelectItem value="12">Top 12 players</SelectItem>
                      <SelectItem value="16">Top 16 players</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              <div className="form-actions">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setShowForm(false)}
                  className="blue-outline-button"
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  className="btn-primary-ios"
                  disabled={!tierData.name.trim()}
                >
                  Create Rating Tier & Generate Join Code
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      );
    };

    const EnhancedRatingTierCard = ({ tier }) => {
      const [groups, setGroups] = useState([]);
      const [showGroupForm, setShowGroupForm] = useState(false);
      const [tierState, setTierState] = useState(tier);
      const [showEditRange, setShowEditRange] = useState(false);
      const [minInput, setMinInput] = useState(tier.min_rating);
      const [maxInput, setMaxInput] = useState(tier.max_rating);

      useEffect(() => {
        setTierState(tier);
        setMinInput(tier.min_rating);
        setMaxInput(tier.max_rating);
        loadGroups();
      }, [tier.id]);

      const loadGroups = async () => {
        try {
          const response = await axios.get(`${API}/rating-tiers/${tier.id}/player-groups`);
          setGroups(response.data);
        } catch (error) {
          console.error("Error loading groups:", error);
        }
      };

      const createGroups = async (groupData) => {
        try {
          await axios.post(`${API}/rating-tiers/${tier.id}/create-groups`, groupData);
          loadGroups();
          setShowGroupForm(false);
          toast({ 
            title: "Player Groups Created!", 
            description: `Groups created with automatic random assignment` 
          });
        } catch (error) {
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to create groups",
            variant: "destructive"
          });
        }
      };

      return (
        <Card className="glass-card-blue rating-tier-card">
          <CardHeader>
            <div className="tier-header">
              <CardTitle className="tier-name">{tier.name}</CardTitle>
              <div className="tier-badges">
                <Badge className="join-code-badge">
                  📋 {tier.join_code}
                </Badge>
                <Badge className="competition-badge">
                  {tier.competition_system === "Team League Format" ? "🏆" : "⚡"} {tier.competition_system}
                </Badge>
              </div>
            </div>
            <div className="tier-actions" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Button size="sm" variant="outline" className="blue-outline-button" onClick={()=> setShowEditRange(v => !v)}>
                {showEditRange ? 'Close' : 'Edit Range'}
              </Button>
            </div>
            {showEditRange && (
              <div className="edit-range" style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <div>
                  <Label>Min</Label>
                  <Input type="number" step="0.1" min="3.0" max="5.5" className="blue-input" value={minInput} onChange={(e)=> setMinInput(parseFloat(e.target.value))} />
                </div>
                <div>
                  <Label>Max</Label>
                  <Input type="number" step="0.1" min="3.0" max="5.5" className="blue-input" value={maxInput} onChange={(e)=> setMaxInput(parseFloat(e.target.value))} />
                </div>
                <Button className="btn-primary-ios" onClick={async ()=>{
                  if (isNaN(minInput) || isNaN(maxInput) || minInput > maxInput) { toast({ title: 'Invalid range', description: 'Min must be <= Max', variant: 'destructive' }); return; }
                  try {
                    const { data } = await axios.patch(`${API}/rating-tiers/${tier.id}`, { min_rating: minInput, max_rating: maxInput });
                    setTierState(data);
                    toast({ title: 'Updated', description: 'Rating range updated' });
                  } catch (err) {
                    toast({ title: 'Error', description: err.response?.data?.detail || 'Failed to update range', variant: 'destructive' });
                  }
                }}>Save</Button>
              </div>
            )}

            <CardDescription>
              Rating: {tierState.min_rating} - {tierState.max_rating} | Max Players: {tierState.max_players}
              {tierState.competition_system === "Team League Format" && (
                <><br/>Playoff Spots: Top {tierState.playoff_spots}</>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="tier-details">
              <div className="join-code-section">
                <h5>📋 Player Join Code</h5>
                <div className="join-code-display">
                  <code className="join-code">{tier.join_code}</code>
                  <div className="qr-actions">
                    <Button 
                      size="icon" 
                      variant="outline" 
                      className="blue-outline-button" 
                      title="Copy Code"
                      onClick={() => {
                        navigator.clipboard.writeText(tier.join_code);
                        toast({ title: "Copied!", description: "Join code copied to clipboard" });
                      }}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                    <div className="qr-popover">
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="blue-outline-button"
                        onClick={(e) => {
                          const el = e.currentTarget.nextSibling;
                          if (el) el.style.display = el.style.display === 'block' ? 'none' : 'block';
                        }}
                      >
                        QR
                      </Button>
                      <div className="qr-card" style={{ display: 'none' }}>
                        <QRCode value={`${window.location.origin}/?join=${tier.join_code}`} size={128} bgColor="transparent" fgColor="#ffffff" />
                      </div>
                    </div>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="blue-outline-button" 
                      onClick={async () => {
                        const url = `${window.location.origin}/?join=${tier.join_code}`;
                        try {
                          if (navigator.share) {
                            await navigator.share({ title: 'Join my League', text: `Join ${tier.name} on LeagueAce`, url });
                          } else {
                            await navigator.clipboard.writeText(url);
                            toast({ title: "Share link copied!", description: url });
                          }
                        } catch (err) {
                          await navigator.clipboard.writeText(url);
                          toast({ title: "Share link copied!", description: url });
                        }
                      }}
                    >
                      Share Join Link
                    </Button>
                  </div>
                </div>
                <p className="join-instructions">Share this code with players to join this rating tier</p>
              </div>

              <div className="groups-section">
                <h5>Player Groups ({groups.length})</h5>
                {groups.length > 0 ? (
                  <div className="groups-list">
                    {groups.map((group) => (
                      <div key={group.id} className="group-item">
                        <Badge className="group-badge">
                          {group.name}
                        </Badge>
                        <span className="group-size">{group.group_size} players</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="no-groups">No groups created yet</p>
                )}
                
                {!showGroupForm ? (
                  <Button 
                    size="sm"
                    className="btn-primary-ios mt-2"
                    onClick={() => setShowGroupForm(true)}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Create Player Groups
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
                <div className="join-code-section">
                  <h5>📋 Player Join Code</h5>
                  <div className="join-code-display">
                    <code className="join-code">{tier.join_code}</code>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="blue-outline-button" 
                      onClick={() => { navigator.clipboard.writeText(tier.join_code); toast({ title: 'Copied!', description: 'Join code copied to clipboard' }); }}
                    >
                      Copy
                    </Button>
                  </div>
                  <p className="join-instructions">Share this code with players to let them join this tier later anytime.</p>
                </div>
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
                <span className="join-share-link">Share link: {`${window.location.origin}/?join=${tier.join_code}`}</span>
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
                    className="btn-primary-ios mt-2"
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
            <Button type="submit" className="btn-primary-ios">
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
              className="btn-primary-ios"
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
              
              <Tabs defaultValue="matches" className="group-tabs">
                <TabsList className="mb-4">
                  <TabsTrigger value="matches">Matches</TabsTrigger>
                  <TabsTrigger value="standings">Standings</TabsTrigger>
                </TabsList>
                
                <TabsContent value="matches">
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
                      className="btn-primary-ios"
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
                        <MatchCard key={match.id} match={match} />
                      ))}
                    </div>
                  )}
                </TabsContent>
                
                <TabsContent value="standings">
                  <StandingsView tierId={tierId} groupId={groupId} />
                </TabsContent>
              </Tabs>
            </div>
          )}
        </div>
      );
    };

    const MatchCard = ({ match }) => {
      const [timeProposals, setTimeProposals] = useState([]);
      const [confirmations, setConfirmations] = useState([]);
      const [showTimeProposal, setShowTimeProposal] = useState(false);
      const [showConfirmation, setShowConfirmation] = useState(false);
      const [tossResult, setTossResult] = useState(null);

      useEffect(() => {
        loadMatchDetails();
      }, [match.id]);

      const loadMatchDetails = async () => {
        try {
          // Load time proposals
          const proposalsResponse = await axios.get(`${API}/matches/${match.id}/time-proposals`);
          setTimeProposals(proposalsResponse.data);

          // Load confirmations
          const confirmationsResponse = await axios.get(`${API}/matches/${match.id}/confirmations`);
          setConfirmations(confirmationsResponse.data);

          // Load toss result if completed
          if (match.toss_completed) {
            try {
              const tossResponse = await axios.get(`${API}/matches/${match.id}/toss`);
              setTossResult(tossResponse.data);
            } catch (error) {
              // Toss not found, which is fine
            }
          }
        } catch (error) {
          console.error("Error loading match details:", error);
        }
      };

      const getStatusColor = (status) => {
        switch (status) {
          case 'Pending': return 'bg-yellow-500/20 text-yellow-200';
          case 'Confirmed': return 'bg-green-500/20 text-green-200';
          case 'Played': return 'bg-blue-500/20 text-blue-200';
          case 'Cancelled': return 'bg-red-500/20 text-red-200';
          default: return 'bg-gray-500/20 text-gray-200';
        }
      };

      return (
        <Card className="glass-card-blue match-card">
          <CardHeader>
            <div className="match-header">
              <CardTitle className="match-title">
                {match.format} Match - Week {match.week_number}
              </CardTitle>
              <Badge className={`match-status ${getStatusColor(match.status)}`}>
                {match.status}
              </Badge>
            </div>
            <CardDescription>
              {match.scheduled_at ? (
                <div className="match-schedule">
                  📅 {new Date(match.scheduled_at).toLocaleDateString()} at{' '}
                  {new Date(match.scheduled_at).toLocaleTimeString()}
                  {match.venue_name && (
                    <>
                      <br />📍 {match.venue_name}
                    </>
                  )}
                </div>
              ) : (
                <span>⏰ Time not set</span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="match-actions">
              {match.status !== 'Played' && (
                <>
                  {match.status === 'Pending' && (
                    <>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="blue-outline-button"
                        onClick={() => setShowTimeProposal(true)}
                      >
                        <Clock className="w-4 h-4 mr-1" />
                        Propose Time
                      </Button>
                      {timeProposals.length > 0 && (
                        <div className="time-proposals">
                          <h6>Time Proposals ({timeProposals.length})</h6>
                          {timeProposals.map((proposal) => (
                            <div key={proposal.id} className="proposal-item">
                              <span>{new Date(proposal.proposed_datetime).toLocaleString()}</span>
                              <Badge variant="outline">{proposal.votes?.length || 0} votes</Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}

                  {match.status === 'Confirmed' && (
                    <>
                      <Button 
                        size="sm" 
                        className="btn-primary-ios"
                        onClick={() => setShowConfirmation(true)}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Confirm Attendance
                      </Button>
                      {!match.toss_completed && (
                        <TossButton matchId={match.id} onTossComplete={loadMatchDetails} />
                      )}
                    </>
                  )}

                  {/* Always show scoring widget so players can enter scores after play */}
                  <ScoringInterface match={match} onScoreUpdate={loadMatchDetails} />

                  {tossResult && (
                    <div className="toss-result">
                      <Badge className="toss-badge">
                        🪙 Toss Winner: {tossResult.winner_id} - {tossResult.choice}
                      </Badge>
                    </div>
                  )}

                  {confirmations.length > 0 && (
                    <div className="confirmations">
                      <h6>Player Confirmations</h6>
                      {confirmations.map((conf) => (
                        <Badge 
                          key={conf.id} 
                          className={conf.status === 'Accepted' ? 'confirmation-accepted' : 'confirmation-pending'}
                        >
                          {conf.status}
                        </Badge>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>

            {showTimeProposal && (
              <TimeProposalForm 
                matchId={match.id}
                onSubmit={() => {
                  setShowTimeProposal(false);
                  loadMatchDetails();
                }}
                onCancel={() => setShowTimeProposal(false)}
              />
            )}

            {showConfirmation && (
              <ConfirmationForm 
                matchId={match.id}
                onSubmit={() => {
                  setShowConfirmation(false);
                  loadMatchDetails();
                }}
                onCancel={() => setShowConfirmation(false)}
              />
            )}
          </CardContent>
        </Card>
      );
    };

    const TimeProposalForm = ({ matchId, onSubmit, onCancel }) => {
      const [proposalData, setProposalData] = useState({
        proposed_datetime: '',
        venue_name: '',
        venue_address: '',
        notes: ''
      });

      const handleSubmit = async (e) => {
        e.preventDefault();
        try {
          await axios.post(`${API}/matches/${matchId}/propose-time`, {
            ...proposalData,
            proposed_datetime: new Date(proposalData.proposed_datetime).toISOString()
          }, {
            params: { proposed_by: user?.id }
          });
          toast({ title: "Success", description: "Match time proposed!" });
          onSubmit();
        } catch (error) {
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to propose time", 
            variant: "destructive" 
          });
        }
      };

      return (
        <form onSubmit={handleSubmit} className="time-proposal-form">
          <div className="form-row">
            <div>
              <Label>Proposed Date & Time</Label>
              <Input
                type="datetime-local"
                value={proposalData.proposed_datetime}
                onChange={(e) => setProposalData({...proposalData, proposed_datetime: e.target.value})}
                className="blue-input"
                required
              />
            </div>
          </div>
          <div>
            <Label>Venue Name (Optional)</Label>
            <Input
              value={proposalData.venue_name}
              onChange={(e) => setProposalData({...proposalData, venue_name: e.target.value})}
              placeholder="Tennis Club, Court Name, etc."
              className="blue-input"
            />
          </div>
          <div>
            <Label>Venue Address (Optional)</Label>
            <Input
              value={proposalData.venue_address}
              onChange={(e) => setProposalData({...proposalData, venue_address: e.target.value})}
              placeholder="123 Main St, City, State"
              className="blue-input"
            />
          </div>
          <div>
            <Label>Notes (Optional)</Label>
            <Textarea
              value={proposalData.notes}
              onChange={(e) => setProposalData({...proposalData, notes: e.target.value})}
              placeholder="Additional details about the proposed time..."
              className="blue-input"
            />
          </div>
          <div className="form-actions">
            <Button type="button" variant="outline" onClick={onCancel} className="blue-outline-button">
              Cancel
            </Button>
            <Button type="submit" className="btn-primary-ios">
              Propose Time
            </Button>
          </div>
        </form>
      );
    };

    const ConfirmationForm = ({ matchId, onSubmit, onCancel }) => {
      const [confirmationData, setConfirmationData] = useState({
        status: 'Accepted',
        notes: ''
      });

      const handleSubmit = async (e) => {
        e.preventDefault();
        try {
          await axios.post(`${API}/matches/${matchId}/confirm`, confirmationData, {
            params: { player_id: user?.id }
          });
          toast({ title: "Success", description: "Match participation confirmed!" });
          onSubmit();
        } catch (error) {
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to confirm participation", 
            variant: "destructive" 
          });
        }
      };

      return (
        <form onSubmit={handleSubmit} className="confirmation-form">
          <div>
            <Label>Participation Status</Label>
            <Select 
              value={confirmationData.status} 
              onValueChange={(value) => setConfirmationData({...confirmationData, status: value})}
            >
              <SelectTrigger className="blue-input">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Accepted">✅ Accept - I'll be there</SelectItem>
                <SelectItem value="Declined">❌ Decline - Can't make it</SelectItem>
                <SelectItem value="Substitute Requested">🔄 Need substitute</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Notes (Optional)</Label>
            <Textarea
              value={confirmationData.notes}
              onChange={(e) => setConfirmationData({...confirmationData, notes: e.target.value})}
              placeholder="Any additional information..."
              className="blue-input"
            />
          </div>
          <div className="form-actions">
            <Button type="button" variant="outline" onClick={onCancel} className="blue-outline-button">
              Cancel
            </Button>
            <Button type="submit" className="btn-primary-ios">
              Submit Confirmation
            </Button>
          </div>
        </form>
      );
    };

    const TossButton = ({ matchId, onTossComplete }) => {
      const [loading, setLoading] = useState(false);

      const conductToss = async () => {
        setLoading(true);
        try {
          const response = await axios.post(`${API}/matches/${matchId}/toss`, 
            { match_id: matchId },
            { params: { initiated_by: user?.id }}
          );
          toast({ 
            title: "🪙 Toss Complete!", 
            description: response.data.message 
          });
          onTossComplete();
        } catch (error) {
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to conduct toss", 
            variant: "destructive" 
          });
        }
        setLoading(false);
      };

      return (
        <Button 
          size="sm" 
          variant="outline" 
          className="blue-outline-button"
          onClick={conductToss}
          disabled={loading}
        >
          <Shuffle className="w-4 h-4 mr-1" />
          {loading ? "Tossing..." : "Coin Toss"}
        </Button>
      );
    };

    const ScoringInterface = ({ match, onScoreUpdate }) => {
      const [sets, setSets] = useState([]);
      const [currentSet, setCurrentSet] = useState(1);
      const [loading, setLoading] = useState(false);

      useEffect(() => {
        loadMatchScore();
      }, [match.id]);

      const loadMatchScore = async () => {
        try {
          const response = await axios.get(`${API}/matches/${match.id}/score`);
          setSets(response.data.sets || []);
          setCurrentSet(response.data.sets?.length + 1 || 1);
        } catch (error) {
          console.error("Error loading match score:", error);
        }
      };

      const updateSetScore = async (setNumber, scoreData) => {
        setLoading(true);
        try {
          await axios.post(`${API}/matches/${match.id}/score-set`, {
            match_id: match.id,
            set_number: setNumber,
            ...scoreData
          }, {
            params: { updated_by: user?.id }
          });
          
          await loadMatchScore();
          if (onScoreUpdate) onScoreUpdate();
          
          toast({ title: "Success", description: "Set score updated!" });
        } catch (error) {
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to update score", 
            variant: "destructive" 
          });
        }
        setLoading(false);
      };

      const submitFinalScore = async (finalScoreData) => {
        setLoading(true);
        try {
          await axios.post(`${API}/matches/${match.id}/submit-final-score`, finalScoreData, {
            params: { submitted_by: user?.id }
          });
          
          await loadMatchScore();
          if (onScoreUpdate) onScoreUpdate();
          
          toast({ title: "Success", description: "Match result submitted!" });
        } catch (error) {
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to submit result", 
            variant: "destructive" 
          });
        }
        setLoading(false);
      };

      if (match.format === 'Doubles') {
        return <DoublesScoring 
          match={match} 
          sets={sets} 
          currentSet={currentSet}
          onUpdateScore={updateSetScore}
          onSubmitFinal={submitFinalScore}
          loading={loading}
        />;
      } else {
        return <SinglesScoring 
          match={match} 
          sets={sets} 
          currentSet={currentSet}
          onUpdateScore={updateSetScore}
          onSubmitFinal={submitFinalScore}
          loading={loading}
        />;
      }
    };

    const DoublesScoring = ({ match, sets, currentSet, onUpdateScore, onSubmitFinal, loading }) => {
      const [teamAScore, setTeamAScore] = useState(0);
      const [teamBScore, setTeamBScore] = useState(0);
      const [isSetComplete, setIsSetComplete] = useState(false);
      const [matchWinner, setMatchWinner] = useState([]);

      const updateScore = () => {
        onUpdateScore(currentSet, {
          team_a_score: teamAScore,
          team_b_score: teamBScore,
          is_set_complete: isSetComplete
        });
        
        if (isSetComplete) {
          setTeamAScore(0);
          setTeamBScore(0);
          setIsSetComplete(false);
        }
      };

      const submitFinalResult = () => {
        const setsData = sets.map((set, index) => ({
          set_number: index + 1,
          team_a_score: set.team_a_score,
          team_b_score: set.team_b_score,
          is_set_complete: true
        }));

        onSubmitFinal({
          match_id: match.id,
          sets: setsData,
          match_winner_ids: matchWinner
        });
      };

      return (
        <Card className="glass-card-blue scoring-interface">
          <CardHeader>
            <CardTitle>🎾 Doubles Match Scoring</CardTitle>
            <CardDescription>Set {currentSet} Score Entry</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="scoring-grid">
              <div className="team-scoring">
                <h4>Team A</h4>
                <div className="score-controls">
                  <Button size="sm" variant="outline" onClick={() => setTeamAScore(Math.max(0, teamAScore - 1))}>
                    -
                  </Button>
                  <span className="score-display">{teamAScore}</span>
                  <Button size="sm" variant="outline" onClick={() => setTeamAScore(Math.min(7, teamAScore + 1))}>
                    +
                  </Button>
                </div>
              </div>

              <div className="vs-divider">vs</div>

              <div className="team-scoring">
                <h4>Team B</h4>
                <div className="score-controls">
                  <Button size="sm" variant="outline" onClick={() => setTeamBScore(Math.max(0, teamBScore - 1))}>
                    -
                  </Button>
                  <span className="score-display">{teamBScore}</span>
                  <Button size="sm" variant="outline" onClick={() => setTeamBScore(Math.min(7, teamBScore + 1))}>
                    +
                  </Button>
                </div>
              </div>
            </div>

            <div className="scoring-actions">
              <div className="set-complete-check">
                <input
                  type="checkbox"
                  id="setComplete"
                  checked={isSetComplete}
                  onChange={(e) => setIsSetComplete(e.target.checked)}
                />
                <Label htmlFor="setComplete">Set Complete</Label>
              </div>

              <Button 
                className="btn-primary-ios" 
                onClick={updateScore}
                disabled={loading}
              >
                {loading ? "Updating..." : "Update Set Score"}
              </Button>
            </div>

            {sets.length > 0 && (
              <div className="sets-summary">
                <h5>Match Score Summary</h5>
                {sets.map((set, index) => (
                  <div key={index} className="set-summary">
                    Set {index + 1}: Team A {set.team_a_score} - {set.team_b_score} Team B
                  </div>
                ))}
                
                {sets.length >= 2 && (
                  <div className="final-submission">
                    <Select value={matchWinner.join(',')} onValueChange={(value) => setMatchWinner(value.split(','))}>
                      <SelectTrigger className="blue-input">
                        <SelectValue placeholder="Select match winner" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={match.participants.slice(0, 2).join(',')}>Team A</SelectItem>
                        <SelectItem value={match.participants.slice(2).join(',')}>Team B</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Button 
                      className="btn-primary-ios mt-2" 
                      onClick={submitFinalResult}
                      disabled={loading || matchWinner.length === 0}
                    >
                      Submit Final Result
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      );
    };

    const SinglesScoring = ({ match, sets, currentSet, onUpdateScore, onSubmitFinal, loading }) => {
      const [player1Score, setPlayer1Score] = useState(0);
      const [player2Score, setPlayer2Score] = useState(0);
      const [isSetComplete, setIsSetComplete] = useState(false);
      const [matchWinner, setMatchWinner] = useState('');

      const updateScore = () => {
        onUpdateScore(currentSet, {
          player1_score: player1Score,
          player2_score: player2Score,
          is_set_complete: isSetComplete
        });
        
        if (isSetComplete) {
          setPlayer1Score(0);
          setPlayer2Score(0);
          setIsSetComplete(false);
        }
      };

      const submitFinalResult = () => {
        const setsData = sets.map((set, index) => ({
          set_number: index + 1,
          player1_score: set.player1_score,
          player2_score: set.player2_score,
          is_set_complete: true
        }));

        onSubmitFinal({
          match_id: match.id,
          sets: setsData,
          match_winner_ids: [matchWinner]
        });
      };

      return (
        <Card className="glass-card-blue scoring-interface">
          <CardHeader>
            <CardTitle>🎾 Singles Match Scoring</CardTitle>
            <CardDescription>Set {currentSet} Score Entry</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="scoring-grid">
              <div className="player-scoring">
                <h4>Player 1</h4>
                <div className="score-controls">
                  <Button size="sm" variant="outline" onClick={() => setPlayer1Score(Math.max(0, player1Score - 1))}>
                    -
                  </Button>
                  <span className="score-display">{player1Score}</span>
                  <Button size="sm" variant="outline" onClick={() => setPlayer1Score(Math.min(7, player1Score + 1))}>
                    +
                  </Button>
                </div>
              </div>

              <div className="vs-divider">vs</div>

              <div className="player-scoring">
                <h4>Player 2</h4>
                <div className="score-controls">
                  <Button size="sm" variant="outline" onClick={() => setPlayer2Score(Math.max(0, player2Score - 1))}>
                    -
                  </Button>
                  <span className="score-display">{player2Score}</span>
                  <Button size="sm" variant="outline" onClick={() => setPlayer2Score(Math.min(7, player2Score + 1))}>
                    +
                  </Button>
                </div>
              </div>
            </div>

            <div className="scoring-actions">
              <div className="set-complete-check">
                <input
                  type="checkbox"
                  id="setComplete"
                  checked={isSetComplete}
                  onChange={(e) => setIsSetComplete(e.target.checked)}
                />
                <Label htmlFor="setComplete">Set Complete</Label>
              </div>

              <Button 
                className="btn-primary-ios" 
                onClick={updateScore}
                disabled={loading}
              >
                {loading ? "Updating..." : "Update Set Score"}
              </Button>
            </div>

            {sets.length > 0 && (
              <div className="sets-summary">
                <h5>Match Score Summary</h5>
                {sets.map((set, index) => (
                  <div key={index} className="set-summary">
                    Set {index + 1}: {set.player1_score} - {set.player2_score}
                  </div>
                ))}
                
                {sets.length >= 2 && (
                  <div className="final-submission">
                    <Select value={matchWinner} onValueChange={setMatchWinner}>
                      <SelectTrigger className="blue-input">
                        <SelectValue placeholder="Select match winner" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={match.participants[0]}>Player 1</SelectItem>
                        <SelectItem value={match.participants[1]}>Player 2</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Button 
                      className="btn-primary-ios mt-2" 
                      onClick={submitFinalResult}
                      disabled={loading || !matchWinner}
                    >
                      Submit Final Result
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      );
    };

    const StandingsView = ({ tierId, groupId }) => {
      const [standings, setStandings] = useState([]);
      const [qualifiers, setQualifiers] = useState([]);
      const [loading, setLoading] = useState(false);

      useEffect(() => {
        loadStandings();
        loadQualifiers();
      }, [tierId, groupId]);

      const loadStandings = async () => {
        setLoading(true);
        try {
          const response = await axios.get(`${API}/rating-tiers/${tierId}/standings`, {
            params: groupId ? { group_id: groupId } : {}
          });
          setStandings(response.data.standings || []);
        } catch (error) {
          console.error("Error loading standings:", error);
        }
        setLoading(false);
      };

      const loadQualifiers = async () => {
        try {
          const response = await axios.get(`${API}/rating-tiers/${tierId}/playoff-qualifiers`);
          setQualifiers(response.data.qualifiers || []);
        } catch (error) {
          // Qualifiers not available yet
        }
      };

      const createPlayoffBracket = async () => {
        try {
          const response = await axios.post(`${API}/rating-tiers/${tierId}/create-playoff-bracket`, {}, {
            params: { created_by: user?.id }
          });
          toast({ title: "Success", description: "Playoff bracket created!" });
          loadQualifiers();
        } catch (error) {
          toast({ 
            title: "Error", 
            description: error.response?.data?.detail || "Failed to create bracket", 
            variant: "destructive" 
          });
        }
      };

      return (
        <Card className="glass-card-blue standings-view">
          <CardHeader>
            <CardTitle>📊 League Standings</CardTitle>
            <CardDescription>Current rankings and playoff qualifications</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="loading-message">Loading standings...</div>
            ) : standings.length > 0 ? (
              <>
                <div className="standings-table">
                  <div className="standings-header">
                    <span>Rank</span>
                    <span>Player</span>
                    <span>Sets Won</span>
                    <span>Sets Played</span>
                    <span>Win %</span>
                    <span>Matches</span>
                  </div>
                  {standings.map((player, index) => (
                    <div key={player.player_id} className={`standings-row ${index < 8 ? 'playoff-qualifier' : ''}`}>
                      <span className="rank">#{player.rank}</span>
                      <span className="player-name">{player.player_id}</span>
                      <span className="sets-won">{player.total_sets_won}</span>
                      <span className="sets-played">{player.total_sets_played}</span>
                      <span className="win-percentage">{(player.set_win_percentage * 100).toFixed(1)}%</span>
                      <span className="matches">{player.matches_played}W-{player.matches_played - player.matches_won}L</span>
                    </div>
                  ))}
                </div>

                {qualifiers.length > 0 && (
                  <div className="playoff-section">
                    <h5>🏆 Playoff Qualifiers (Top 8)</h5>
                    <div className="qualifiers-list">
                      {qualifiers.map((qualifier, index) => (
                        <Badge key={qualifier.player_id} className="qualifier-badge">
                          #{qualifier.rank} {qualifier.player_name}
                        </Badge>
                      ))}
                    </div>
                    
                    <Button 
                      className="btn-primary-ios mt-3"
                      onClick={createPlayoffBracket}
                    >
                      Create Playoff Bracket
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <div className="no-standings">
                <p>No standings available yet. Complete some matches to see rankings!</p>
              </div>
            )}
          </CardContent>
        </Card>
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
                      className="btn-primary-ios"
                      onClick={() => setShowCreateLeague(true)}
                    >
                      <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
                      Create New {activeSport} League
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <CreateLeagueForm />
              )}
            </div>

            {/* Persisted Leagues list so managers always see leagues after refresh */}
            <div className="tier-section">
              <h3 className="tier-title">Your {activeSport} Leagues</h3>
              <div className="leagues-grid">
                {leagues.length === 0 ? (
                  <Card className="glass-card-blue empty-state-card">
                    <CardContent className="empty-state">
                      <div className="empty-icon">🏆</div>
                      <h4>No leagues yet</h4>
                      <p>Create your first league to get started. It will persist and appear here after refresh.</p>
                    </CardContent>
                  </Card>
                ) : (
                  leagues.map((league) => (
                    <Card 
                      key={league.id}
                      className={`glass-card-blue league-card ${selectedLeague?.id === league.id ? 'selected' : ''}`}
                      onClick={() => {
                        setSelectedLeague(league);
                        setActiveManagerTab('four-tier');
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
                  ))
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="four-tier">
            <FourTierManagement />
            <div className="tier-section" style={{ marginTop: 16 }}>
              <h3 className="tier-title">Join Requests</h3>
              <Card className="glass-card-blue">
                <CardContent>
                  <JoinRequestsPanel />
                </CardContent>
              </Card>
            </div>
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
  // Profile picture components
  const ProfilePicture = ({ user, size = "md" }) => {
    const dim = size === "lg" ? 64 : size === "sm" ? 28 : 40;
    const initials = (user?.name || "?").trim().charAt(0).toUpperCase();
    const src = user?.profile_picture;
    if (src) {
      return (
        <img
          src={src}
          alt="Profile"
          width={dim}
          height={dim}
          className="profile-picture"
          style={{ width: dim, height: dim }}
        />
      );
    }
    return (
      <div
        className="profile-picture-placeholder"
        style={{ width: dim, height: dim }}
        aria-label="Profile placeholder"
      >
        {initials}
      </div>
    );
  };

  const ProfilePictureUpload = ({ onUploadComplete }) => {
    const [busy, setBusy] = useState(false);
    const inputRef = useRef(null);

    const pickFile = () => inputRef.current?.click();

    const onFileChange = async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setBusy(true);
      try {
        await handleProfilePictureUpload(file);
        const res = await axios.get(`${API}/users/${user.id}`);
        onUploadComplete?.(res.data);
      } catch (err) {
        toast({ title: "Error", description: "Failed to upload picture", variant: "destructive" });
      }
      setBusy(false);
    };

    const removePicture = async () => {
      setBusy(true);
      try {
        await axios.post(`${API}/users/${user.id}/remove-picture`);
        const res = await axios.get(`${API}/users/${user.id}`);
        onUploadComplete?.(res.data);
      } catch (err) {
        toast({ title: "Error", description: "Failed to remove picture", variant: "destructive" });
      }
      setBusy(false);
    };

    return (
      <div className="profile-picture-upload">
        <div className="profile-picture-container">
          <div className="upload-target" onClick={pickFile} role="button" tabIndex={0}>
            <ProfilePicture user={user} size="lg" />
          </div>
          <div className="upload-overlay" onClick={pickFile}>
            {busy ? (
              <span className="upload-spinner">⏳</span>
            ) : (
              <>
                <Camera className="w-5 h-5 mr-1" /> Upload
              </>
            )}
          </div>
        </div>
        <input ref={inputRef} type="file" accept="image/*" onChange={onFileChange} style={{ display: 'none' }} />
        <div className="upload-actions">
          <Button variant="outline" className="blue-outline-button" type="button" onClick={pickFile} disabled={busy}>
            <Upload className="w-4 h-4 mr-1" /> Choose Image
          </Button>
          <Button variant="outline" className="blue-outline-button" type="button" onClick={removePicture} disabled={busy}>
            Remove
          </Button>
        </div>
      </div>
    );
  };


  // Continue with Player Dashboard and other components...
  // (Player Dashboard, Navigation, etc. remain similar but updated for new structure)



  const PlayerDashboard = () => {
    const [activePlayerTab, setActivePlayerTab] = useState('home');
    const [showJoinForm, setShowJoinForm] = useState(false);
  const pendingURLJoinCode = useRef(null);

  useEffect(() => {
    const code = getPendingJoinCodeFromURL();
    if (code) {
      pendingURLJoinCode.current = code;
      setJoinCode(code);
      setShowJoinForm(true);
    }
    // Partner token acceptance via URL
    const params = new URLSearchParams(window.location.search);
    const partnerToken = params.get('partner');
    if (partnerToken && user?.id) {
      axios.post(`${API}/doubles/invites/accept`, { token: partnerToken, invitee_user_id: user.id })
        .then(async ({ data }) => {
          toast({ title: 'Doubles Team Created', description: `${data.team_name}` });
          // Clean URL param
          const url = new URL(window.location.href); url.searchParams.delete('partner'); window.history.replaceState({}, '', url);
          setActivePlayerTab('doubles');
        })
        .catch((e) => {
          const detail = e?.response?.data?.detail || 'Failed to accept invite';
          toast({ title: 'Error', description: detail, variant: 'destructive' });
        });
    }
  }, [user]);
    const [joinCode, setJoinCode] = useState("");
    const [upcomingMatches, setUpcomingMatches] = useState([]);

    useEffect(() => {
      loadUpcomingMatches();
    }, [user, activeSport]);

    const loadUpcomingMatches = async () => {
      if (user) {
        try {
          // This would load matches for the player - simplified for now
          const response = await axios.get(`${API}/users/${user.id}/matches?sport_type=${activeSport}`);
          setUpcomingMatches(response.data || []);
        } catch (error) {
          console.error("Error loading matches:", error);
        }
      }
    };

    const [joinPreview, setJoinPreview] = useState(null);
    const [joinPreviewError, setJoinPreviewError] = useState("");

    useEffect(() => {
      const lookup = async () => {
        const code = (joinCode || '').trim().toUpperCase();
        if (code.length === 6) {
          try {
            const { data } = await axios.get(`${API}/rating-tiers/by-code/${code}`);
            setJoinPreview(data);
            setJoinPreviewError("");
          } catch (err) {
            setJoinPreview(null);
            setJoinPreviewError("Invalid join code");
          }
        } else {
          setJoinPreview(null);
          setJoinPreviewError("");
        }
      };
      lookup();
    }, [joinCode]);

    const handleJoinByCode = async (e) => {
      e.preventDefault();
      setLoading(true);
      try {
        const code = (joinCode || '').trim().toUpperCase();
        if (code.length !== 6) {
          toast({ title: 'Invalid code', description: 'Join code must be 6 characters', variant: 'destructive' });
          setLoading(false);
          return;
        }
        // Optional: pre-validate code so we can show league name before joining
        try {
          const { data: tierSummary } = await axios.get(`${API}/rating-tiers/by-code/${code}`);
          if (tierSummary?.league_name) {
            toast({ title: `Joining ${tierSummary.league_name}`, description: `${tierSummary.name} • Rating ${tierSummary.min_rating}-${tierSummary.max_rating}` });
          }
        } catch (err) {
          /* no-op, backend will give exact reason on join */
        }
        await axios.post(`${API}/join-by-code/${user.id}`, { join_code: code });
        await loadPlayerData();
        setShowJoinForm(false);
        setJoinCode("");
        setJoinPreview(null);
        toast({ title: "Success", description: "Successfully joined league!" });
      } catch (error) {
        console.error("Error joining by code:", error);
        const detail = error?.response?.data?.detail || "Failed to join league";
        setJoinPreviewError(detail);
        toast({ 
          title: "Error", 
          description: detail,
          variant: "destructive"
        });
      }
      setLoading(false);
    };

    const PlayerHome = () => (
      <div className="player-home">
        <div className="welcome-section">
          <Card className="glass-card-blue">
            <CardHeader>
              <CardTitle>Welcome back, {user.name}!</CardTitle>
              <CardDescription>Your {activeSport} league activity at a glance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="stats-grid">
                <div className="stat-item">
                  <h4>{userJoinedTiers.length}</h4>
                  <p>Leagues Joined</p>
                </div>
                <div className="stat-item">
                  <h4>{upcomingMatches.length}</h4>
                  <p>Upcoming Matches</p>
                </div>
                <div className="stat-item">
                  <h4>{userStandings.length}</h4>
                  <p>Active Tournaments</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <Card className="glass-card-blue">
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="action-buttons">
                <Button 
                  className="btn-primary-ios"
                  onClick={() => setActivePlayerTab('leagues')}
                >
                  <span className="icon-glass-container"><Users className="w-4 h-4 mr-2" /></span>
                  View My Leagues
                </Button>
                <Button 
                  className="btn-primary-ios"
                  onClick={() => setActivePlayerTab('schedule')}
                >
                  <span className="icon-glass-container"><Calendar className="w-4 h-4 mr-2" /></span>
                  View Schedule
                </Button>
                <Button 
                  className="blue-outline-button"
                  onClick={() => setShowJoinForm(true)}
                >
                  <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
                  Join New League
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        {notifications.length > 0 && (
          <div className="recent-activity">
            <Card className="glass-card-blue">
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                {notifications.slice(0, 3).map((notification) => (
                  <div key={notification.id} className="notification-item">
                    <p>{notification.message}</p>
                    <span className="notification-time">
                      {new Date(notification.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    );

    const PlayerLeagues = () => (
      <div className="player-leagues">
        <div className="leagues-header">
          <h3>My {activeSport} Leagues</h3>
          <Button 
            className="btn-primary-ios"
            onClick={() => setShowJoinForm(true)}
          >
            <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
            Join New League
          </Button>
        </div>

        {userJoinedTiers.length > 0 ? (
          <div className="joined-leagues-grid">
            {userJoinedTiers.map((tier) => (
              <Card key={tier.id} className="glass-card-blue league-card">
                <CardHeader>
                  <CardTitle>{tier.name}</CardTitle>
                  <CardDescription>
                    Rating: {tier.min_rating} - {tier.max_rating}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="league-info">
                    <Badge className="competition-badge">
                      {tier.competition_system}
                    </Badge>
                    <div className="league-stats">
                      <div className="join-code-display">
                        <span>Join Code:</span>
                        <code>{tier.join_code}</code>
                        <Button
                          size="icon"
                          variant="ghost"
                          title="Copy Code"
                          onClick={() => navigator.clipboard?.writeText(tier.join_code)}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <div className="qr-popover">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="blue-outline-button"
                            onClick={(e) => {
                              const el = e.currentTarget.nextSibling;
                              if (el) el.style.display = el.style.display === 'block' ? 'none' : 'block';
                            }}
                          >
                            QR
                          </Button>
                          <div className="qr-card" style={{ display: 'none' }}>
                            <QRCode value={`${window.location.origin}/?join=${tier.join_code}`} size={128} bgColor="transparent" fgColor="#ffffff" />
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          className="blue-outline-button"
                          onClick={async () => {
                            const url = `${window.location.origin}/?join=${tier.join_code}`;
                            try {
                              if (navigator.share) {
                                await navigator.share({ title: 'Join my League', text: `Join ${tier.name} on LeagueAce`, url });
                              } else {
                                await navigator.clipboard.writeText(url);
                                toast({ title: 'Share link copied!', description: url });
                              }
                            } catch (err) {
                              await navigator.clipboard.writeText(url);
                              toast({ title: 'Share link copied!', description: url });
                            }
                          }}
                        >
                          Share
                        </Button>
                      </div>
                      <p>Players: {tier.current_players || 0}/{tier.max_players}</p>
                    </div>
                  </div>
                  <div className="league-actions">
                    <Button 
                      size="sm"
                      className="blue-outline-button"
                      onClick={() => setActivePlayerTab('standings')}
                    >
                      View Standings
                    </Button>
                    <Button 
                      size="sm"
                      className="btn-primary-ios"
                      onClick={() => setActivePlayerTab('chat')}
                    >
                      League Chat
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="glass-card-blue empty-state-card">
            <CardContent className="empty-state">
              <div className="empty-icon">🎾</div>
              <h4>No Leagues Joined Yet</h4>
              <p>Join a league using a 6-character code from your league manager</p>
              <Button 
                className="btn-primary-ios"
                onClick={() => setShowJoinForm(true)}
              >
                <span className="icon-glass-container"><Plus className="w-4 h-4 mr-2" /></span>
                Join Your First League
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    );

    const PlayerSchedule = () => (
      <div className="player-schedule">
        <Card className="glass-card-blue">
          <CardHeader>
            <CardTitle>Match Schedule</CardTitle>
            <CardDescription>Your upcoming {activeSport} matches</CardDescription>
          </CardHeader>
          <CardContent>
            {upcomingMatches.length > 0 ? (
              <div className="matches-list">
                {upcomingMatches.map((match) => (
                  <div key={match.id} className="match-item">
                    <div className="match-info">
                      <h5>{match.format} Match - Week {match.week_number}</h5>
                      <p>{match.scheduled_at ? new Date(match.scheduled_at).toLocaleString() : 'Time TBD'}</p>
                      <Badge className={getMatchStatusColor(match.status)}>
                        {match.status}
                      </Badge>
                    </div>
                    <div className="match-actions">
                      <Button size="sm" className="blue-outline-button">
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>No upcoming matches scheduled</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );

    const PlayerDoubles = () => {
      const [teams, setTeams] = useState([]);
      const [creatingInvite, setCreatingInvite] = useState(false);
      const [invitePreview, setInvitePreview] = useState(null);
      const [inviteContact, setInviteContact] = useState('');
      const [linkToken, setLinkToken] = useState('');
      const [tierCode, setTierCode] = useState('');
      const [incomingInvites, setIncomingInvites] = useState([]);
      const [outgoingInvites, setOutgoingInvites] = useState([]);

      const [expanded, setExpanded] = useState({});
      const [prefsByTeam, setPrefsByTeam] = useState({});
      const [matchesByTeam, setMatchesByTeam] = useState({});
      const [standingsByTier, setStandingsByTier] = useState({});

      const loadTeams = async () => {
        try {
          const { data } = await axios.get(`${API}/doubles/teams`, { params: { player_id: user.id } });
          setTeams(data || []);
        } catch (e) {
          console.error('Failed to load doubles teams', e);
        }
      };

      const loadInvites = async () => {
        try {
          const inc = await axios.get(`${API}/doubles/invites`, { params: { user_id: user.id, role: 'incoming' } });
          const out = await axios.get(`${API}/doubles/invites`, { params: { user_id: user.id, role: 'outgoing' } });
          setIncomingInvites(inc.data?.invites || []);
          setOutgoingInvites(out.data?.invites || []);
        } catch (e) {
          console.error('Failed to load invites', e);
        }
      };

      const loadPrefs = async (team) => {
        try {
          const { data } = await axios.get(`${API}/doubles/teams/${team.id}/preferences`);
          setPrefsByTeam(prev => ({ ...prev, [team.id]: data }));
        } catch (e) {
          toast({ title: 'Error', description: 'Failed to load preferences', variant: 'destructive' });
        }
      };

      const savePrefs = async (team) => {
        const pref = prefsByTeam[team.id];
        try {
          const { data } = await axios.put(`${API}/doubles/teams/${team.id}/preferences`, pref);
          setPrefsByTeam(prev => ({ ...prev, [team.id]: data }));
          toast({ title: 'Saved', description: 'Team preferences updated' });
        } catch (e) {
          toast({ title: 'Error', description: e?.response?.data?.detail || 'Failed to save preferences', variant: 'destructive' });
        }
      };

      const loadMatches = async (team) => {
        try {
          const { data } = await axios.get(`${API}/doubles/matches`, { params: { team_id: team.id } });
          setMatchesByTeam(prev => ({ ...prev, [team.id]: data || [] }));
        } catch (e) {
          toast({ title: 'Error', description: 'Failed to load matches', variant: 'destructive' });
        }
      };

      const proposeSlot = async (matchId, slot) => {
        try {
          await axios.post(`${API}/doubles/matches/${matchId}/propose-slots`, { slots: [slot], proposed_by_user_id: user.id });
          toast({ title: 'Proposed', description: 'Slot proposed to both teams' });
          // reload matches for the team owning this match
          const team = teams.find(t => matchesByTeam[t.id]?.some(m => m.id === matchId));
          if (team) await loadMatches(team);
        } catch (e) {
          toast({ title: 'Error', description: e?.response?.data?.detail || 'Failed to propose', variant: 'destructive' });
        }
      };

      const confirmSlot = async (matchId, slotId) => {
        try {
          const { data } = await axios.post(`${API}/doubles/matches/${matchId}/confirm-slot`, { slot_id: slotId, user_id: user.id });
          if (data.locked) toast({ title: 'Scheduled', description: 'Match confirmed and scheduled' });
          else toast({ title: 'Confirmed', description: 'Your confirmation recorded' });
          const team = teams.find(t => matchesByTeam[t.id]?.some(m => m.id === matchId));
          if (team) await loadMatches(team);
        } catch (e) {
          toast({ title: 'Error', description: e?.response?.data?.detail || 'Failed to confirm', variant: 'destructive' });
        }
      };

      const submitScore = async (matchId, sets) => {
        try {
          await axios.post(`${API}/doubles/matches/${matchId}/submit-score`, { sets, submitted_by_user_id: user.id });
          toast({ title: 'Score submitted', description: 'Awaiting co-sign' });
        } catch (e) {
          toast({ title: 'Error', description: e?.response?.data?.detail || 'Failed to submit score', variant: 'destructive' });
        }
      };

      const cosignScore = async (matchId) => {
        try {
          await axios.post(`${API}/doubles/matches/${matchId}/co-sign`, { user_id: user.id, role: 'partner' });
          toast({ title: 'Co-signed', description: 'Thanks for confirming' });
          const team = teams.find(t => matchesByTeam[t.id]?.some(m => m.id === matchId));
          if (team) await loadMatches(team);
        } catch (e) {
          toast({ title: 'Error', description: e?.response?.data?.detail || 'Failed to co-sign', variant: 'destructive' });
        }
      };

      const downloadICS = async (matchId) => {
        try {
          const { data } = await axios.get(`${API}/doubles/matches/${matchId}/ics`);
          const blob = new Blob([data.ics], { type: 'text/calendar;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `match-${matchId}.ics`;
          a.click();
          URL.revokeObjectURL(url);
        } catch (e) {
          toast({ title: 'Not ready', description: 'ICS available only after match is confirmed', variant: 'destructive' });
        }
      };

      const loadStandings = async (tierId) => {
        try {
          const { data } = await axios.get(`${API}/doubles/standings`, { params: { rating_tier_id: tierId } });
          setStandingsByTier(prev => ({ ...prev, [tierId]: data || [] }));
        } catch (e) {
          toast({ title: 'Error', description: 'Failed to load standings', variant: 'destructive' });
        }
      };

      useEffect(() => { loadTeams(); }, [user]);

      const createInvite = async () => {
        if (!tierCode) {
          toast({ title: 'Tier required', description: 'Enter the doubles tier join code or select from UI later', variant: 'destructive' });
          return;
        }
        setCreatingInvite(true);
        try {
          const { data } = await axios.post(`${API}/doubles/invites`, { inviter_user_id: user.id, join_code: tierCode });
          setInvitePreview(data);
          setLinkToken(data.token);
          toast({ title: 'Invite created', description: 'Share the link or QR with your partner' });
        } catch (e) {
          toast({ title: 'Error', description: e?.response?.data?.detail || 'Failed to create invite', variant: 'destructive' });
        }
        setCreatingInvite(false);
      };

      const shareUrl = linkToken ? `${window.location.origin}/?partner=${linkToken}` : '';

      const addAvailabilityRow = (teamId) => {
        setPrefsByTeam(prev => {
          const p = prev[teamId] || { team_id: teamId, preferred_venues: [], availability: [], max_subs: 0 };
          const next = { ...p, availability: [...(p.availability||[]), { day: 'Wed', start: '18:00', end: '21:00' }] };
          return { ...prev, [teamId]: next };
        });
      };

      const updatePrefField = (teamId, field, value) => {
        setPrefsByTeam(prev => ({ ...prev, [teamId]: { ...(prev[teamId]||{ team_id: teamId, availability: [], preferred_venues: [], max_subs: 0 }), [field]: value } }));
      };

      const updateAvailability = (teamId, idx, key, val) => {
        setPrefsByTeam(prev => {
          const p = prev[teamId];
          if (!p) return prev;
          const av = [...(p.availability||[])];
          av[idx] = { ...av[idx], [key]: val };
          return { ...prev, [teamId]: { ...p, availability: av } };
        });
      };

      return (
        <div className="player-standings">
          <Card className="glass-card-blue">
            <CardHeader>
              <CardTitle>My Doubles Teams</CardTitle>
              <CardDescription>Create a partner link, manage schedules, and score matches</CardDescription>
            </CardHeader>
            <CardContent>
              {teams.length > 0 ? (
                <div className="standings-list">
                  {teams.map((t) => (
                    <div key={t.id} className="standing-item">
                      <div className="standing-rank">🎾</div>
                      <div className="standing-info">
                        <h5>{t.team_name}</h5>
                        <p>{t.league_name} • {t.rating_tier_name}</p>
                        <p>Members: {t.members?.map(m => m.name).join(', ')}</p>
                        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                          <Button size="sm" className="btn-outline-ios" onClick={async ()=>{ setExpanded(e=>({...e,[t.id]:!e[t.id]})); if(!expanded[t.id]){ await loadPrefs(t); await loadMatches(t); } }}>
                            {expanded[t.id] ? 'Hide' : 'Manage'}
                          </Button>
                          <Button size="sm" className="btn-outline-ios" onClick={()=> loadStandings(t.rating_tier_id)}>View Standings</Button>
                          <Button size="sm" className="btn-outline-ios" onClick={()=> loadMatches(t)}>Refresh Matches</Button>
                        </div>
                      </div>

                      {expanded[t.id] && (
                        <div className="glass-subcard" style={{ marginTop: 12, width: '100%' }}>
                          {/* Preferences */}
                          <div style={{ padding: 12 }}>
                            <h6 style={{ fontWeight: 600, marginBottom: 8 }}>Team Preferences</h6>
                            <div className="grid" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 8 }}>
                              <div>
                                <Label>Preferred Venues (comma separated)</Label>
                                <Input value={(prefsByTeam[t.id]?.preferred_venues||[]).join(', ')} onChange={(e)=> updatePrefField(t.id, 'preferred_venues', e.target.value.split(',').map(s=>s.trim()).filter(Boolean))} placeholder="Court A, Court B" />
                              </div>
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <Label>Weekly Availability</Label>
                                  <Button size="sm" variant="outline" onClick={()=> addAvailabilityRow(t.id)}>Add Window</Button>
                                </div>
                                <div>
                                  {(prefsByTeam[t.id]?.availability||[]).map((w, idx)=> (
                                    <div key={idx} style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                                      <select value={w.day} onChange={(e)=> updateAvailability(t.id, idx, 'day', e.target.value)}>
                                        {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(d=> <option key={d} value={d}>{d}</option>)}
                                      </select>
                                      <Input className="w-28" value={w.start} onChange={(e)=> updateAvailability(t.id, idx, 'start', e.target.value)} placeholder="18:00" />
                                      <Input className="w-28" value={w.end} onChange={(e)=> updateAvailability(t.id, idx, 'end', e.target.value)} placeholder="21:00" />
                                    </div>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <Label>Max Subs</Label>
                                <Input type="number" min={0} value={prefsByTeam[t.id]?.max_subs||0} onChange={(e)=> updatePrefField(t.id, 'max_subs', parseInt(e.target.value||'0',10))} className="w-24" />
                              </div>
                              <div>
                                <Button className="btn-primary-ios" onClick={()=> savePrefs(t)}>Save Preferences</Button>
                              </div>
                            </div>
                          </div>

                          {/* Matches */}
                          <div style={{ padding: 12, marginTop: 8 }}>
                            <h6 style={{ fontWeight: 600, marginBottom: 8 }}>Matches</h6>
                            <div className="standings-list">
                              {(matchesByTeam[t.id]||[]).map(m => (
                                <div key={m.id} className="standing-item">
                                  <div className="standing-rank">📅</div>
                                  <div className="standing-info" style={{ width: '100%' }}>
                                    <h5>{m.team1_name} vs {m.team2_name}</h5>
                                    <p>Status: {m.status}</p>
                                    {m.status === 'CONFIRMED' && (
                                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                        <Button size="sm" variant="outline" onClick={()=> downloadICS(m.id)}>Download ICS</Button>
                                        <span>{m.scheduled_at ? new Date(m.scheduled_at).toLocaleString() : ''} {m.scheduled_venue ? `• ${m.scheduled_venue}` : ''}</span>
                                      </div>
                                    )}

                                    {/* Proposed slots */}
                                    <div style={{ marginTop: 8 }}>
                                      <Label>Proposed Slots</Label>
                                      <div>
                                        {(m.proposed_slots||[]).map(s => (
                                          <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                                            <span>{new Date(s.start).toLocaleString()} {s.venue_name ? `• ${s.venue_name}` : ''}</span>
                                            <Button size="sm" className="btn-outline-ios" onClick={()=> confirmSlot(m.id, s.id)}>Confirm</Button>
                                          </div>
                                        ))}
                                      </div>
                                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 8 }}>
                                        <Input type="datetime-local" className="w-60" onChange={(e)=> m._newStart = e.target.value} />
                                        <Input className="w-48" placeholder="Venue (optional)" onChange={(e)=> m._venue = e.target.value} />
                                        <Button size="sm" className="btn-primary-ios" onClick={()=> {
                                          if (!m._newStart) { toast({ title: 'Pick a time', variant: 'destructive' }); return; }
                                          const iso = new Date(m._newStart).toISOString();
                                          proposeSlot(m.id, { start: iso, venue_name: m._venue });
                                        }}>Propose Slot</Button>
                                      </div>
                                    </div>

                                    {/* Scoring */}
                                    <div style={{ marginTop: 12 }}>
                                      <Label>Submit Score (best-of-3)</Label>
                                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 6 }}>
                                        <Input className="w-16" placeholder="6" onChange={(e)=> m._s1 = parseInt(e.target.value||'0',10)} />
                                        <Input className="w-16" placeholder="4" onChange={(e)=> m._s2 = parseInt(e.target.value||'0',10)} />
                                        <Input className="w-16" placeholder="3" onChange={(e)=> m._s3 = parseInt(e.target.value||'0',10)} />
                                        <Input className="w-16" placeholder="6" onChange={(e)=> m._t3 = parseInt(e.target.value||'0',10)} />
                                        <Button size="sm" className="btn-primary-ios" onClick={()=> {
                                          const sets = [];
                                          if (!isNaN(m._s1) && !isNaN(m._s2)) sets.push({ team1_games: m._s1, team2_games: m._s2 });
                                          if (!isNaN(m._s3) && !isNaN(m._t3)) sets.push({ team1_games: m._s3, team2_games: m._t3 });
                                          if (sets.length === 0) { toast({ title: 'Add at least 1 set', variant: 'destructive' }); return; }
                                          submitScore(m.id, sets);
                                        }}>Submit</Button>
                                        <Button size="sm" className="btn-outline-ios" onClick={()=> cosignScore(m.id)}>Co-sign</Button>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Standings */}
                          {standingsByTier[t.rating_tier_id] && (
                            <div style={{ padding: 12, marginTop: 8 }}>
                              <h6 style={{ fontWeight: 600, marginBottom: 8 }}>Standings</h6>
                              <div className="standings-list">
                                {standingsByTier[t.rating_tier_id].map((row)=> (
                                  <div key={row.id} className="standing-item">
                                    <div className="standing-rank">🏆</div>
                                    <div className="standing-info">
                                      <h5>{row.team_name}</h5>
                                      <p>Pts: {row.points} • W-L: {row.wins}-{row.losses} • Sets: {row.sets_won}-{row.sets_lost} • Games: {row.games_won}-{row.games_lost}</p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p>No doubles teams yet. Create an invite to pair with your partner.</p>
                </div>
              )}

              <div className="tier-creator" style={{ marginTop: 16 }}>
                <Label>Enter Doubles Tier Join Code</Label>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <Input value={tierCode} onChange={(e)=> setTierCode((e.target.value||'').toUpperCase())} maxLength={6} className="blue-input w-32" placeholder="e.g., ABC123" />
                  <Button className="btn-primary-ios" disabled={creatingInvite || (tierCode||'').length !== 6} onClick={createInvite}>
                    {creatingInvite ? 'Creating…' : 'Create Partner Link'}
                  </Button>
                </div>
              </div>

              {linkToken && (
                <div style={{ marginTop: 16 }}>
                  <div className="join-code-display">
                    <span>Partner Link:</span>
                    <code style={{ overflowWrap: 'anywhere' }}>{shareUrl}</code>
                    <Button size="icon" variant="ghost" title="Copy Link" onClick={() => navigator.clipboard?.writeText(shareUrl)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                    <div className="qr-popover">
                      <Button size="sm" variant="outline" className="blue-outline-button" onClick={(e)=>{
                        const el = e.currentTarget.nextSibling; if (el) el.style.display = el.style.display === 'block' ? 'none' : 'block';
                      }}>QR</Button>
                      <div className="qr-card" style={{ display: 'none' }}>
                        <QRCode value={shareUrl} size={128} bgColor="transparent" fgColor="#ffffff" />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      );
    };

    const PlayerStandings = () => (
      <div className="player-standings">
        <Card className="glass-card-blue">
          <CardHeader>
            <CardTitle>League Standings</CardTitle>
            <CardDescription>Your ranking in joined leagues</CardDescription>
          </CardHeader>
          <CardContent>
            {userStandings.length > 0 ? (
              <div className="standings-list">
                {userStandings.map((standing, index) => (
                  <div key={index} className="standing-item">
                    <div className="standing-rank">#{standing.rank || 'N/A'}</div>
                    <div className="standing-info">
                      <h5>{standing.league_name}</h5>
                      <p>Sets Won: {standing.total_sets_won || 0}/{standing.total_sets_played || 0}</p>
                      <p>Win Rate: {(standing.set_win_percentage * 100 || 0).toFixed(1)}%</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>No standings available yet. Join a league to see your rankings!</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );

    const PlayerChat = () => {
      const [threads, setThreads] = useState([]);
      const [activeThread, setActiveThread] = useState(null);
      const [messages, setMessages] = useState([]);
      const [chatInput, setChatInput] = useState("");
      const [loadingChat, setLoadingChat] = useState(false);

      useEffect(() => {
        loadThreads();
      }, [userJoinedTiers, upcomingMatches]);

      useEffect(() => {
        if (activeThread) {
          loadMessages(activeThread.id);
        }
      }, [activeThread]);

      const loadThreads = async () => {
        try {
          // Heuristic: show a synthetic thread for each joined tier until dedicated endpoint exists
          const syntheticThreads = (userJoinedTiers || []).map(t => ({
            id: t.chat_thread_id || t.id, // fall back to tier id
            name: `${t.league_name || "League"} • ${t.name}`,
            type: 'league'
          }));
          setThreads(syntheticThreads);
          if (syntheticThreads[0]) setActiveThread(syntheticThreads[0]);
        } catch (e) {
          console.error('Error loading chat threads', e);
        }
      };

      const loadMessages = async (threadId) => {
        setLoadingChat(true);
        try {
          const res = await axios.get(`${API}/chat/threads/${threadId}/messages`, { params: { user_id: user?.id, limit: 50 } });
          setMessages(res.data || []);
        } catch (e) {
          // If backend denies due to membership check, present empty feed gracefully
          setMessages([]);
        }
        setLoadingChat(false);
      };

      const sendMessage = async (e) => {
        e.preventDefault();
        if (!chatInput.trim() || !activeThread) return;
        const text = chatInput.trim();
        setChatInput("");
        try {
          await axios.post(`${API}/chat/messages`, {
            thread_id: activeThread.id,
            text
          }, { params: { sender_id: user?.id } });
          await loadMessages(activeThread.id);
        } catch (e) {
          toast({ title: 'Error', description: e.response?.data?.detail || 'Failed to send message', variant: 'destructive' });
        }
      };

      return (
        <div className="player-chat">
          <Card className="glass-card-blue">
            <CardHeader>
              <CardTitle>League Chat</CardTitle>
              <CardDescription>Messages from your leagues</CardDescription>
            </CardHeader>
            <CardContent>
              {threads.length === 0 ? (
                <div className="empty-state">
                  <p>No chat threads yet. Join a league to start chatting.</p>
                </div>
              ) : (
                <div className="chat-panel">
                  <div>
                    <Label>Thread</Label>
                    <Select value={activeThread?.id || ''} onValueChange={(id) => setActiveThread(threads.find(t => t.id === id))}>
                      <SelectTrigger className="blue-input">
                        <SelectValue placeholder="Select a thread" />
                      </SelectTrigger>
                      <SelectContent>
                        {threads.map(t => (
                          <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="chat-feed">
                    {loadingChat ? (
                      <div className="loading-message">Loading messages…</div>
                    ) : messages.length === 0 ? (
                      <div className="empty-state">No messages yet.</div>
                    ) : (
                      messages.map(m => (
                        <div key={m.id} className="chat-message">
                          <div>
                            <div>{m.text}</div>
                            <div className="chat-meta">{new Date(m.created_at).toLocaleString()}</div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                  <form onSubmit={sendMessage} className="chat-input-row">
                    <Input value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Type a message…" className="blue-input" />
                    <Button className="btn-primary-ios" type="submit">
                      <span className="icon-glass-container"><Send className="w-4 h-4" /></span>
                    </Button>
                  </form>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      );
    };

    const PlayerProfile = () => {
      const [editName, setEditName] = useState(user.name || "");
      const [editPhone, setEditPhone] = useState(user.phone || "");
      const [saving, setSaving] = useState(false);

      useEffect(() => {
        setEditName(user.name || "");
        setEditPhone(user.phone || "");
      }, [user]);

      const sanitizePhone = (val) => {
        // Allow only + and digits
        return (val || "").replace(/[^+0-9]/g, "");
      };
      const phoneDigits = editPhone.replace(/\D/g, "");
      const phoneValid = editPhone.length === 0 || phoneDigits.length >= 7; // optional, but if present >=7 digits
      const changed = (editName.trim() !== (user.name || "")) || (editPhone !== (user.phone || ""));

      const saveProfile = async () => {
        if (!changed || !phoneValid) return;
        setSaving(true);
        try {
          const payload = {};
          if (editName.trim() !== (user.name || "")) payload.name = editName.trim();
          if (editPhone !== (user.phone || "")) payload.phone = editPhone;
          const { data } = await axios.patch(`${API}/users/${user.id}`, payload);
          setUser(data);
          toast({ title: 'Saved', description: 'Profile updated successfully' });
        } catch (err) {
          toast({ title: 'Error', description: err.response?.data?.detail || 'Failed to save profile', variant: 'destructive' });
        }
        setSaving(false);
      };

      const resetChanges = () => {
        setEditName(user.name || "");
        setEditPhone(user.phone || "");
      };

      return (
        <div className="player-profile">
          <Card className="glass-card-blue">
            <CardHeader>
              <CardTitle>Player Profile</CardTitle>
              <CardDescription>Manage your profile information and picture</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="profile-content">
                <div className="profile-picture-section">
                  <h5>Profile Picture</h5>
                  <ProfilePictureUpload onUploadComplete={(updatedUser) => setUser(updatedUser)} />
                </div>

                <div className="profile-info">
                  <div className="info-grid">
                    <div className="info-item">
                      <Label htmlFor="edit-name">Name</Label>
                      <Input id="edit-name" value={editName} className="blue-input" onChange={(e)=> setEditName(e.target.value)} />
                    </div>
                    <div className="info-item">
                      <Label>Email</Label>
                      <p>{user.email}</p>
                    </div>
                    <div className="info-item">
                      <Label htmlFor="edit-phone">Mobile</Label>
                      <Input id="edit-phone" value={editPhone} className="blue-input" onChange={(e)=> setEditPhone(sanitizePhone(e.target.value))} />
                      {!phoneValid && (<div className="join-error">Please enter at least 7 digits (digits and + only)</div>)}
                    </div>
                    <div className="info-item">
                      <Label>Rating Level</Label>
                      <p>{user.rating_level}</p>
                    </div>
                    <div className="info-item">
                      <Label>Sport Preferences</Label>
                      <p>{user.sports_preferences?.join(', ') || 'None set'}</p>
                    </div>
                  </div>

                  <div className="profile-actions" style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                    <Button className="btn-primary-ios" disabled={!changed || !phoneValid || saving} onClick={saveProfile}>
                      {saving ? 'Saving…' : 'Save'}
                    </Button>
                    <Button variant="outline" className="blue-outline-button" disabled={!changed || saving} onClick={resetChanges}>Cancel</Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    };

    const getMatchStatusColor = (status) => {
      switch (status) {
        case 'Pending': return 'bg-yellow-500/20 text-yellow-200';
        case 'Confirmed': return 'bg-green-500/20 text-green-200';
        case 'Played': return 'bg-blue-500/20 text-blue-200';
        default: return 'bg-gray-500/20 text-gray-200';
      }
    };

    return (
      <div className="player-dashboard">
        <div className="dashboard-header">
          <div className="header-left">
            <ProfilePicture user={user} size="lg" />
            <div className="header-text">
              <h2 className="section-title-blue">{activeSport} Player Dashboard</h2>
              <p>Welcome back, {user.name}!</p>
            </div>
          </div>
          <div className="dashboard-user-info">
            <span>Rating: {user.rating_level}</span>
            <Badge className="role-badge-blue">Player</Badge>
          </div>
        </div>

        <Tabs value={activePlayerTab} onValueChange={setActivePlayerTab} className="dashboard-tabs">
          <TabsList className="tabs-list">
            <TabsTrigger value="home">Home</TabsTrigger>
            <TabsTrigger value="leagues">My Leagues</TabsTrigger>
            <TabsTrigger value="doubles">My Doubles Teams</TabsTrigger>
            <TabsTrigger value="schedule">Schedule</TabsTrigger>
            <TabsTrigger value="standings">Standings</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
          </TabsList>

          <TabsContent value="home" className="tab-content">
            <PlayerHome />
          </TabsContent>

          <TabsContent value="leagues" className="tab-content">
            <PlayerLeagues />
          </TabsContent>

          <TabsContent value="doubles" className="tab-content">
            <PlayerDoubles />
          </TabsContent>

          <TabsContent value="schedule" className="tab-content">
            <PlayerSchedule />
          </TabsContent>

          <TabsContent value="standings" className="tab-content">
            <PlayerStandings />
          </TabsContent>

          <TabsContent value="profile" className="tab-content">
            <PlayerProfile />
          </TabsContent>

          <TabsContent value="chat" className="tab-content">
            <PlayerChat />
          </TabsContent>
        </Tabs>

        {/* Join League Modal */}
        {showJoinForm && (
          <div className="modal-overlay">
            <Card className="glass-card-blue join-modal">
              <CardHeader>
                <CardTitle>Join a {activeSport} League</CardTitle>
                <CardDescription>
                  Enter the 6-character join code provided by your league manager
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleJoinByCode} className="join-form">
                  <div className="form-group">
                    <Label htmlFor="join-code">League Join Code</Label>
                    <Input
                      id="join-code"
                      type="text"
                      placeholder="Enter 6-character code"
                      value={joinCode}
                      onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                      className="blue-input"
                      maxLength="6"
                      required
                    />
                    {joinPreview && (
                      <div className="join-preview">
                        <div className="preview-title">{joinPreview.league_name || 'League'}</div>
                        <div className="preview-sub">{joinPreview.name} • Rating {joinPreview.min_rating}-{joinPreview.max_rating}</div>
                        <div className="preview-sub">Join link: {`${window.location.origin}/?join=${joinCode}`}</div>
                        {user && (user.rating_level < joinPreview.min_rating || user.rating_level > joinPreview.max_rating) && (
                          <div className="join-error">Your rating {user.rating_level} is outside this tier range. Please choose a different tier or ask your manager to adjust the tier range.</div>
                        )}
                      </div>
                    )}
                    {!joinPreview && joinPreviewError && (
                      <div className="join-error">{joinPreviewError}</div>
                    )}
                    {joinPreview && user && (user.rating_level < joinPreview.min_rating || user.rating_level > joinPreview.max_rating) && (
                      <div className="join-error" style={{ marginTop: 8 }}>
                        You can request manager approval to join this tier.
                        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                          <Input placeholder="Add a note (optional)" className="blue-input" onChange={(e)=> window.__joinNote = e.target.value} />
                          <Button className="btn-primary-ios" onClick={async ()=>{
                            try {
                              const { data } = await axios.post(`${API}/join-requests`, { user_id: user.id, rating_tier_id: joinPreview.id, message: window.__joinNote || '' });
                              toast({ title: 'Request sent', description: 'Manager will review your request shortly.' });
                            } catch (err) {
                              toast({ title: 'Error', description: err.response?.data?.detail || 'Failed to send request', variant: 'destructive' });
                            }
                          }}>Request to Join</Button>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="form-actions">
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={() => {
                        setShowJoinForm(false);
                        setJoinCode("");
                      }}
                      className="blue-outline-button"
                    >
                      Cancel
                    </Button>
                    <Button 
                      type="submit" 
                      className="btn-primary-ios"
                      disabled={loading || joinCode.length !== 6 || (joinPreview && user && (user.rating_level < joinPreview.min_rating || user.rating_level > joinPreview.max_rating))}
                    >
                      {loading ? "Joining..." : "Join League"}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}
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
                className="btn-nav-ios"
              >
                <span className="icon-glass-container"><Shield className="w-4 h-4 mr-2" /></span>
                Dashboard
              </Button>
            </div>
          ) : (
            <div className="nav-tabs">
              <Button
                variant={activeTab === "home" ? "default" : "ghost"}
                onClick={() => setActiveTab("home")}
                className="btn-nav-ios"
              >
                <span className="icon-glass-container"><Calendar className="w-4 h-4 mr-2" /></span>
                Home
              </Button>
            </div>
          )}
          
          <div className="nav-user">
            <div className="notification-bell-blue">
              <span className="icon-glass-container"><Bell className="w-5 h-5" /></span>
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