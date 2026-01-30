import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUpload.css';

interface FileUploadProps {
  onUpload: (file: File) => void;
  onLoadSample: () => void;
  isUploading: boolean;
}

function FileUpload({ onUpload, onLoadSample, isUploading }: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles[0]);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/gzip': ['.nii.gz'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
    maxFiles: 1,
    disabled: isUploading,
  });

  return (
    <div className="file-upload-container">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${isUploading ? 'disabled' : ''}`}
      >
        <input {...getInputProps()} />

        {isUploading ? (
          <div className="upload-progress">
            <div className="spinner"></div>
            <p>Uploading...</p>
          </div>
        ) : isDragActive ? (
          <div className="drop-message">
            <span className="icon">+</span>
            <p>Drop the file here</p>
          </div>
        ) : (
          <div className="upload-message">
            <span className="icon">+</span>
            <p>Drag & drop MRI file here</p>
            <p className="sub">or click to select</p>
            <p className="formats">Supported: NIfTI (.nii.gz), PNG, JPEG</p>
          </div>
        )}
      </div>

      <div className="sample-section">
        <p>No test file?</p>
        <button
          className="sample-button"
          onClick={onLoadSample}
          disabled={isUploading}
        >
          Use Sample MRI
        </button>
        <p className="sample-credit">
          Data: <a href="https://doi.org/10.1038/s41597-025-04427-9" target="_blank" rel="noopener noreferrer">TOM500</a> (Zhang H, et al. 2025) - CC BY 4.0
        </p>
      </div>
    </div>
  );
}

export default FileUpload;
