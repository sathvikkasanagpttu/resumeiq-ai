import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, NavTab } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { ResumeIntelligencePage } from './pages/ResumeIntelligencePage';
import { JobAnalyzerPage } from './pages/JobAnalyzerPage';
import { MatchAnalysisPage } from './pages/MatchAnalysisPage';
import { SkillGapsPage } from './pages/SkillGapsPage';
import { ResumeOptimizerPage } from './pages/ResumeOptimizerPage';
import { ApplicationGeneratorPage } from './pages/ApplicationGeneratorPage';
import { CareerRoadmapPage } from './pages/CareerRoadmapPage';
import { JobRecommendationsPage } from './pages/JobRecommendationsPage';
import { MarketAnalyticsPage } from './pages/MarketAnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './services/api';
import { Resume, Job } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);

  useEffect(() => {
    // Initial data load
    refreshData();
  }, []);

  const refreshData = async () => {
    try {
      const [rList, jList] = await Promise.all([
        api.listResumes(),
        api.listJobs()
      ]);
      setResumes(rList);
      setJobs(jList);

      if (rList.length > 0 && !selectedResumeId) {
        setSelectedResumeId(rList[0].id);
      }
      if (jList.length > 0 && !selectedJobId) {
        setSelectedJobId(jList[0].id);
      }
    } catch (e) {
      console.error('Failed to load initial dataset', e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />

      <div className="flex flex-1">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={(tab) => setCurrentTab(tab)}
        />

        <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full overflow-x-hidden">
          {currentTab === 'dashboard' && (
            <DashboardPage
              onNavigate={(tab) => setCurrentTab(tab)}
              onSelectResume={(id) => setSelectedResumeId(id)}
              onSelectJob={(id) => setSelectedJobId(id)}
              onSelectMatch={(id) => setSelectedMatchId(id)}
            />
          )}

          {currentTab === 'resume-intelligence' && (
            <ResumeIntelligencePage
              selectedResumeId={selectedResumeId}
              onSelectResume={(id) => {
                setSelectedResumeId(id);
                refreshData();
              }}
            />
          )}

          {currentTab === 'job-analyzer' && (
            <JobAnalyzerPage
              selectedJobId={selectedJobId}
              onSelectJob={(id) => {
                setSelectedJobId(id);
                refreshData();
              }}
              onNavigateToMatch={() => setCurrentTab('match-analysis')}
            />
          )}

          {currentTab === 'match-analysis' && (
            <MatchAnalysisPage
              selectedMatchId={selectedMatchId}
              resumes={resumes}
              jobs={jobs}
              onSelectMatch={(id) => setSelectedMatchId(id)}
              onNavigateToGaps={() => setCurrentTab('skill-gaps')}
            />
          )}

          {currentTab === 'skill-gaps' && (
            <SkillGapsPage
              selectedMatchId={selectedMatchId}
              onNavigateToRoadmap={() => setCurrentTab('career-roadmap')}
            />
          )}

          {currentTab === 'resume-optimizer' && (
            <ResumeOptimizerPage
              selectedMatchId={selectedMatchId}
              onNavigateToApplications={() => setCurrentTab('application-generator')}
            />
          )}

          {currentTab === 'application-generator' && (
            <ApplicationGeneratorPage
              selectedMatchId={selectedMatchId}
            />
          )}

          {currentTab === 'career-roadmap' && (
            <CareerRoadmapPage
              selectedMatchId={selectedMatchId}
            />
          )}

          {currentTab === 'job-recommendations' && (
            <JobRecommendationsPage
              selectedResumeId={selectedResumeId}
              onSelectJob={(id) => setSelectedJobId(id)}
              onNavigateToMatch={() => setCurrentTab('match-analysis')}
            />
          )}

          {currentTab === 'market-analytics' && (
            <MarketAnalyticsPage
              selectedResumeId={selectedResumeId}
            />
          )}

          {currentTab === 'settings' && (
            <SettingsPage />
          )}
        </main>
      </div>
    </div>
  );
};
export default App;
