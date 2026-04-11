// components/Documents/UploadZone.jsx
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocument } from '../../services/api';
import toast from 'react-hot-toast';

export default function UploadZone({ onUploaded }) {
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;
    if (!file.name.endsWith('.pdf')) {
      toast.error('Seuls les fichiers PDF sont acceptés');
      return;
    }

    setUploading(true);
    const toastId = toast.loading(`Upload : ${file.name}`);

    try {
      const res = await uploadDocument(file);
      toast.success(
        `✅ ${file.name} reçu ! Indexation GPT-4o en cours...`,
        { id: toastId, duration: 5000 }
      );
      if (onUploaded) onUploaded(res);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erreur upload';
      toast.error(msg, { id: toastId });
    } finally {
      setUploading(false);
    }
  }, [onUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}
    >
      <input {...getInputProps()} />
      <span className="upload-icon">{uploading ? '⏳' : '📄'}</span>
      <div className="upload-text">
        {uploading ? (
          <>Traitement GPT-4o Vision...</>
        ) : isDragActive ? (
          <>Déposez le PDF ici</>
        ) : (
          <><strong>Upload PDF</strong><br />Glissez ou cliquez</>
        )}
      </div>
      <div className="upload-hint">PDF juridique arabe — max 50MB</div>
      {uploading && <div className="upload-progress"><div className="upload-progress-bar" /></div>}
    </div>
  );
}
