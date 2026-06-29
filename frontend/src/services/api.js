const BASE_URL = 'http://localhost:8000/api';

export const fetchDocuments = async () => {
  const response = await fetch(`${BASE_URL}/documents`);
  if (!response.ok) throw new Error('Failed to fetch documents');
  return response.json();
};

export const uploadDocument = async (file, tags, author, collectionId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tags', tags);
  formData.append('author', author);
  formData.append('collectionId', collectionId);

  const response = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error('Failed to upload document');
  return response.json();
};

export const deleteDocument = async (documentId) => {
  const response = await fetch(`${BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete document');
  return response.json();
};

export const chatQuery = async (query, model, collectionId) => {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, model, collectionId }),
  });
  if (!response.ok) throw new Error('Failed to process chat query');
  return response.json();
};

export const checkHealth = async () => {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    if (!response.ok) return false;
    const data = await response.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
};
