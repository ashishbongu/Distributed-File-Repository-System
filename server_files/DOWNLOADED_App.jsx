import { useEffect, useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProblemProvider, useProblem } from './context/ProblemContext';
import { DiscussionProvider, useDiscussion } from './context/DiscussionContext';
import Header from './components/Header';
import ProblemCard from './components/ProblemCard';
import DiscussionCard from './components/DiscussionCard';
import DiscussionDetail from './pages/DiscussionDetail';
import './App.css';

const HomePage = () => {
  const { problems, loading: problemsLoading, fetchProblems } = useProblem();
  const { discussions, loading: discussionsLoading, fetchDiscussions } = useDiscussion();
  const [activeTab, setActiveTab] = useState('problems');

  useEffect(() => {
    fetchProblems();
    fetchDiscussions();
  }, [fetchProblems, fetchDiscussions]);

  const loading = activeTab === 'problems' ? problemsLoading : discussionsLoading;
  const items = activeTab === 'problems' ? problems : discussions;

  return (
    <div className="home-page">
      <div className="container">
        <div className="page-header">
          <h1>Campus Community</h1>
          <p>Report problems and discuss campus topics</p>
        </div>

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'problems' ? 'active' : ''}`}
            onClick={() => setActiveTab('problems')}
          >
            🔧 Problems
          </button>
          <button
            className={`tab ${activeTab === 'discussions' ? 'active' : ''}`}
            onClick={() => setActiveTab('discussions')}
          >
            💬 Discussions
          </button>
        </div>

        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading {activeTab}...</p>
          </div>
        ) : items.length > 0 ? (
          <div className="items-list">
            {activeTab === 'problems'
              ? items.map((problem) => <ProblemCard key={problem.id} problem={problem} />)
              : items.map((discussion) => <DiscussionCard key={discussion.id} discussion={discussion} />)
            }
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">{activeTab === 'problems' ? '📋' : '💬'}</div>
            <h2>No {activeTab} yet</h2>
            <p>Be the first to {activeTab === 'problems' ? 'report an issue' : 'start a discussion'}!</p>
          </div>
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <ProblemProvider>
        <DiscussionProvider>
          <div className="app">
            <Routes>
              <Route path="/" element={
                <>
                  <Header />
                  <HomePage />
                </>
              } />
              <Route path="/discussion/:id" element={<DiscussionDetail />} />
            </Routes>
          </div>
        </DiscussionProvider>
      </ProblemProvider>
    </AuthProvider>
  );
}

export default App;
