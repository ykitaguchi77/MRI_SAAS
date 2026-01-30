import { useState, useEffect, useCallback } from 'react';
import type { FileInfo, SliceData, ClassStatistics } from './types';
import { uploadFile, loadSample, runSegmentation, getResults, checkHealth } from './services/api';
import FileUpload from './components/FileUpload/FileUpload';
import ImageViewer from './components/Visualization/ImageViewer';
import SliceSlider from './components/Visualization/SliceSlider';
import OverlayControls from './components/Visualization/OverlayControls';
import ColorLegend from './components/Visualization/ColorLegend';
import ResultsPanel from './components/Results/ResultsPanel';
import LoadingSpinner from './components/common/LoadingSpinner';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [currentSlice, setCurrentSlice] = useState(0);
  const [totalSlices, setTotalSlices] = useState(1);
  const [overlayAlpha, setOverlayAlpha] = useState(0.5);
  const [viewMode, setViewMode] = useState<'original' | 'mask' | 'overlay'>('overlay');

  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoadingResults, setIsLoadingResults] = useState(false);

  const [sliceData, setSliceData] = useState<SliceData | null>(null);
  const [overallStats, setOverallStats] = useState<ClassStatistics[]>([]);
  const [processingTime, setProcessingTime] = useState<number | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Check API health on mount
  useEffect(() => {
    checkHealth()
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));
  }, []);

  // Load results when slice changes
  const loadSliceResults = useCallback(async (slice: number, alpha: number) => {
    if (!sessionId) return;

    setIsLoadingResults(true);
    try {
      const results = await getResults(sessionId, slice, alpha);
      setSliceData(results.slice_data);
      setTotalSlices(results.total_slices);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setIsLoadingResults(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId && overallStats.length > 0) {
      loadSliceResults(currentSlice, overlayAlpha);
    }
  }, [currentSlice, overlayAlpha, sessionId, overallStats.length, loadSliceResults]);

  const handleUpload = async (file: File) => {
    setError(null);
    setIsUploading(true);

    try {
      const response = await uploadFile(file);
      setSessionId(response.session_id);
      setFileInfo(response.file_info);
      setTotalSlices(response.file_info.num_slices);
      setCurrentSlice(Math.floor(response.file_info.num_slices / 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLoadSample = async () => {
    setError(null);
    setIsUploading(true);

    try {
      const response = await loadSample();
      setSessionId(response.session_id);
      setFileInfo(response.file_info);
      setTotalSlices(response.file_info.num_slices);
      setCurrentSlice(Math.floor(response.file_info.num_slices / 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sample');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSegment = async () => {
    if (!sessionId) return;

    setError(null);
    setIsProcessing(true);

    try {
      const response = await runSegmentation(sessionId);
      setOverallStats(response.statistics);
      setProcessingTime(response.processing_time_ms);

      // Load initial results
      await loadSliceResults(currentSlice, overlayAlpha);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Segmentation failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setSessionId(null);
    setFileInfo(null);
    setSliceData(null);
    setOverallStats([]);
    setProcessingTime(null);
    setCurrentSlice(0);
    setTotalSlices(1);
    setError(null);
  };

  const hasResults = overallStats.length > 0;

  return (
    <div className="app">
      <header className="app-header">
        <h1>MRI T2 Coronal Segmentation</h1>
        <div className="api-status">
          <span className={`status-dot ${apiStatus}`}></span>
          {apiStatus === 'checking' ? 'Checking...' : apiStatus === 'online' ? 'API Online' : 'API Offline'}
        </div>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        {!sessionId ? (
          <section className="upload-section">
            <FileUpload onUpload={handleUpload} onLoadSample={handleLoadSample} isUploading={isUploading} />
          </section>
        ) : (
          <div className="workspace">
            <div className="workspace-left">
              <div className="file-info-card">
                <h3>Uploaded File</h3>
                <p><strong>Name:</strong> {fileInfo?.filename}</p>
                <p><strong>Type:</strong> {fileInfo?.file_type}</p>
                <p><strong>Dimensions:</strong> {fileInfo?.dimensions.join(' x ')}</p>
                <p><strong>Slices:</strong> {fileInfo?.num_slices}</p>

                {!hasResults && (
                  <button
                    className="segment-button"
                    onClick={handleSegment}
                    disabled={isProcessing}
                  >
                    {isProcessing ? 'Processing...' : 'Run Segmentation'}
                  </button>
                )}

                <button className="reset-button" onClick={handleReset}>
                  Upload New File
                </button>
              </div>

              {hasResults && (
                <>
                  <OverlayControls
                    viewMode={viewMode}
                    onViewModeChange={setViewMode}
                    overlayAlpha={overlayAlpha}
                    onAlphaChange={setOverlayAlpha}
                  />
                  <ColorLegend statistics={sliceData?.statistics || []} />
                </>
              )}
            </div>

            <div className="workspace-center">
              {isProcessing ? (
                <div className="processing-overlay">
                  <LoadingSpinner />
                  <p>Running segmentation...</p>
                </div>
              ) : hasResults && sliceData ? (
                <>
                  <ImageViewer
                    originalImage={sliceData.original_image}
                    segmentationMask={sliceData.segmentation_mask}
                    overlayImage={sliceData.overlay_image}
                    viewMode={viewMode}
                    isLoading={isLoadingResults}
                  />

                  {totalSlices > 1 && (
                    <SliceSlider
                      currentSlice={currentSlice}
                      totalSlices={totalSlices}
                      onChange={setCurrentSlice}
                    />
                  )}
                </>
              ) : (
                <div className="empty-viewer">
                  <p>Click "Run Segmentation" to process the image</p>
                </div>
              )}
            </div>

            {hasResults && (
              <div className="workspace-right">
                <ResultsPanel
                  sessionId={sessionId}
                  statistics={overallStats}
                  processingTime={processingTime}
                  fileType={fileInfo?.file_type || 'image'}
                />
              </div>
            )}
          </div>
        )}
      </main>

      {!sessionId && (
        <footer className="app-footer">
          <p>
            Created by <a href="https://researchmap.jp/ykitaguchi" target="_blank" rel="noopener noreferrer">Yoshiyuki Kitaguchi</a>
          </p>
        </footer>
      )}
    </div>
  );
}

export default App;
