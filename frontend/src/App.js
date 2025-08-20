import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Calendar, Users, Trophy, Settings, Plus, TrendingUp, Clock, MapPin } from "lucide-react";
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
  const [activeTab, setActiveTab] = useState("home");
  const [user, setUser] = useState(null);
  const [leagues, setLeagues] = useState([]);
  const [seasons, setSeasons] = useState([]);
  const [matches, setMatches] = useState([]);
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(false);

  // Demo user for testing
  useEffect(() => {
    const demoUser = {
      id: "demo-user-1",
      name: "Alex Rodriguez",
      email: "alex@example.com",
      rating_level: 4.0,
      roles: ["Player"]
    };
    setUser(demoUser);
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [leaguesRes, seasonsRes] = await Promise.all([
        axios.get(`${API}/leagues`),
        axios.get(`${API}/seasons`)
      ]);
      setLeagues(leaguesRes.data);
      setSeasons(seasonsRes.data);
    } catch (error) {
      console.error("Error loading data:", error);
    }
  };

  const loadMatches = async (seasonId) => {
    try {
      const response = await axios.get(`${API}/seasons/${seasonId}/matches`);
      setMatches(response.data);
    } catch (error) {
      console.error("Error loading matches:", error);
    }
  };

  const loadStandings = async (seasonId) => {
    try {
      const response = await axios.get(`${API}/seasons/${seasonId}/standings`);
      setStandings(response.data);
    } catch (error) {
      console.error("Error loading standings:", error);
    }
  };

  const CreateUserForm = () => {
    const [formData, setFormData] = useState({
      name: "",
      email: "",
      phone: "",
      rating_level: 3.5
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      try {
        const response = await axios.post(`${API}/users`, formData);
        setUser(response.data);
        setActiveTab("home");
      } catch (error) {
        console.error("Error creating user:", error);
      }
      setLoading(false);
    };

    return (
      <Card className="glass-card max-w-md mx-auto mt-8">
        <CardHeader>
          <CardTitle className="gradient-text">Join Netly</CardTitle>
          <CardDescription>Create your tennis & pickleball profile</CardDescription>
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
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
              />
            </div>
            <div>
              <Label htmlFor="phone">Phone (Optional)</Label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
              />
            </div>
            <div>
              <Label htmlFor="rating">Skill Rating (3.0-5.5)</Label>
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
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="sport-button w-full" disabled={loading}>
              {loading ? "Creating..." : "Create Profile"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    );
  };

  const CreateLeagueForm = () => {
    const [formData, setFormData] = useState({
      name: "",
      region: "",
      level: "",
      format: "Doubles",
      surface: "Hard Court",
      rules_md: ""
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      try {
        await axios.post(`${API}/leagues`, formData);
        loadData();
        setActiveTab("leagues");
      } catch (error) {
        console.error("Error creating league:", error);
      }
      setLoading(false);
    };

    return (
      <Card className="glass-card max-w-md mx-auto mt-8">
        <CardHeader>
          <CardTitle className="gradient-text">Create New League</CardTitle>
          <CardDescription>Set up a tennis or pickleball league</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="league-name">League Name</Label>
              <Input
                id="league-name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="e.g., Downtown Tennis League"
                required
              />
            </div>
            <div>
              <Label htmlFor="region">Region</Label>
              <Input
                id="region"
                value={formData.region}
                onChange={(e) => setFormData({...formData, region: e.target.value})}
                placeholder="e.g., San Francisco, NYC"
                required
              />
            </div>
            <div>
              <Label htmlFor="level">Level</Label>
              <Select value={formData.level} onValueChange={(value) => setFormData({...formData, level: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select skill level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Beginner (3.0-3.5)">Beginner (3.0-3.5)</SelectItem>
                  <SelectItem value="Intermediate (3.5-4.0)">Intermediate (3.5-4.0)</SelectItem>
                  <SelectItem value="Advanced (4.0-4.5)">Advanced (4.0-4.5)</SelectItem>
                  <SelectItem value="Expert (4.5+)">Expert (4.5+)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="format">Format</Label>
              <Select value={formData.format} onValueChange={(value) => setFormData({...formData, format: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Doubles">Doubles</SelectItem>
                  <SelectItem value="Singles">Singles</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="rules">League Rules (Optional)</Label>
              <Textarea
                id="rules"
                value={formData.rules_md}
                onChange={(e) => setFormData({...formData, rules_md: e.target.value})}
                placeholder="Describe league rules and guidelines..."
              />
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="sport-button w-full" disabled={loading}>
              {loading ? "Creating..." : "Create League"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    );
  };

  const HomeView = () => (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Welcome to <span className="gradient-text">Netly</span>
          </h1>
          <p className="hero-subtitle">
            The premier tennis & pickleball league management platform
          </p>
          {user && (
            <div className="user-welcome">
              <h2>Hello, {user.name}!</h2>
              <Badge variant="secondary" className="sport-badge">
                Rating: {user.rating_level}
              </Badge>
            </div>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="stats-grid">
        <Card className="glass-card stat-card">
          <CardContent className="p-6">
            <div className="stat-content">
              <Users className="stat-icon" />
              <div>
                <p className="stat-number">{leagues.length}</p>
                <p className="stat-label">Active Leagues</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass-card stat-card">
          <CardContent className="p-6">
            <div className="stat-content">
              <Calendar className="stat-icon" />
              <div>
                <p className="stat-number">{seasons.length}</p>
                <p className="stat-label">Seasons</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass-card stat-card">
          <CardContent className="p-6">
            <div className="stat-content">
              <Trophy className="stat-icon" />
              <div>
                <p className="stat-number">{matches.length}</p>
                <p className="stat-label">Matches Played</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {leagues.length > 0 ? (
            <div className="space-y-3">
              {leagues.slice(0, 3).map((league) => (
                <div key={league.id} className="activity-item">
                  <TrendingUp className="activity-icon" />
                  <div>
                    <p className="font-medium">{league.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {league.format} • {league.level}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No recent activity. Join a league to get started!</p>
          )}
        </CardContent>
      </Card>
    </div>
  );

  const LeaguesView = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="section-title">Leagues</h2>
        <Button 
          onClick={() => setActiveTab("create-league")} 
          className="sport-button"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create League
        </Button>
      </div>
      
      <div className="leagues-grid">
        {leagues.map((league) => (
          <Card key={league.id} className="glass-card league-card">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="league-title">{league.name}</CardTitle>
                  <CardDescription>{league.region}</CardDescription>
                </div>
                <Badge className="sport-badge">{league.format}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="league-details">
                <div className="detail-item">
                  <MapPin className="detail-icon" />
                  <span>{league.surface}</span>
                </div>
                <div className="detail-item">
                  <TrendingUp className="detail-icon" />
                  <span>{league.level}</span>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button className="sport-button w-full">View Details</Button>
            </CardFooter>
          </Card>
        ))}
      </div>
      
      {leagues.length === 0 && (
        <Card className="glass-card">
          <CardContent className="p-8 text-center">
            <Trophy className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No leagues found</h3>
            <p className="text-muted-foreground mb-4">
              Create your first league to start organizing matches
            </p>
            <Button onClick={() => setActiveTab("create-league")} className="sport-button">
              Create League
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const ScheduleView = () => (
    <div className="space-y-6">
      <h2 className="section-title">Schedule</h2>
      
      {matches.length > 0 ? (
        <div className="space-y-4">
          {matches.map((match) => (
            <Card key={match.id} className="glass-card">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Week {match.week_number} - {match.format}</CardTitle>
                  <Badge variant={match.status === "Played" ? "default" : "secondary"}>
                    {match.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {match.sets && match.sets.map((set, index) => (
                  <div key={set.id} className="match-set">
                    <div className="set-header">
                      <h4>Set {index + 1}</h4>
                    </div>
                    <div className="teams-display">
                      <div className="team">
                        <span className="team-label">Team A:</span>
                        <span>{set.team_a_names?.join(" & ") || "TBD"}</span>
                        <Badge variant="outline">{set.score_a}</Badge>
                      </div>
                      <div className="vs-divider">VS</div>
                      <div className="team">
                        <span className="team-label">Team B:</span>
                        <span>{set.team_b_names?.join(" & ") || "TBD"}</span>
                        <Badge variant="outline">{set.score_b}</Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="glass-card">
          <CardContent className="p-8 text-center">
            <Calendar className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No matches scheduled</h3>
            <p className="text-muted-foreground">
              Matches will appear here once leagues generate weekly schedules
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const StandingsView = () => (
    <div className="space-y-6">
      <h2 className="section-title">Standings</h2>
      
      {standings.length > 0 ? (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Season Leaderboard</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="standings-table">
              <div className="standings-header">
                <span>Rank</span>
                <span>Player</span>
                <span>Rating</span>
                <span>Wins</span>
                <span>Played</span>
                <span>Win %</span>
              </div>
              {standings.map((standing) => (
                <div key={standing.player_name} className="standings-row">
                  <span className="rank-badge">{standing.rank}</span>
                  <span className="player-name">{standing.player_name}</span>
                  <span>{standing.rating_level}</span>
                  <span>{standing.total_set_wins}</span>
                  <span>{standing.total_sets_played}</span>
                  <span>{(standing.win_pct * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="glass-card">
          <CardContent className="p-8 text-center">
            <Trophy className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No standings available</h3>
            <p className="text-muted-foreground">
              Standings will appear once matches are played and scores are submitted
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  if (!user) {
    return (
      <div className="app-container">
        <CreateUserForm />
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Navigation */}
      <nav className="nav-glass">
        <div className="nav-brand">
          <h1 className="nav-logo">Netly</h1>
        </div>
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
            variant={activeTab === "leagues" ? "default" : "ghost"}
            onClick={() => setActiveTab("leagues")}
            className="nav-button"
          >
            <Users className="w-4 h-4 mr-2" />
            Leagues
          </Button>
          <Button
            variant={activeTab === "schedule" ? "default" : "ghost"}
            onClick={() => setActiveTab("schedule")}
            className="nav-button"
          >
            <Clock className="w-4 h-4 mr-2" />
            Schedule
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
        <div className="nav-user">
          <Badge className="user-badge">
            {user.name}
          </Badge>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === "home" && <HomeView />}
        {activeTab === "leagues" && <LeaguesView />}
        {activeTab === "schedule" && <ScheduleView />}
        {activeTab === "standings" && <StandingsView />}
        {activeTab === "create-league" && <CreateLeagueForm />}
      </main>
    </div>
  );
}

export default App;