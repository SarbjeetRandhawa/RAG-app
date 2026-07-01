const BASE_URL = 'http://localhost:8000/api';

export const fetchDocuments = async () => {
  const response = await fetch(`${BASE_URL}/documents`);
  if (!response.ok) throw new Error('Failed to fetch documents');
  return response.json();
};

export const fetchAnalytics = async () => {
  const response = await fetch(`${BASE_URL}/analytics`);
  if (!response.ok) throw new Error('Failed to fetch analytics');
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

export const chatQuery = async (query, model, collectionId, onMessage) => {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, model, collectionId }),
  });
  if (!response.ok) throw new Error('Failed to process chat query');
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalData = {};

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop(); 
    
    for (const line of lines) {
      if (line.trim()) {
        const parsed = JSON.parse(line);
        if (parsed.type === "chunk") {
          if (onMessage) onMessage(parsed.text);
        } else if (parsed.type === "final") {
          finalData = parsed.data;
        } else if (parsed.type === "error") {
          throw new Error(parsed.error);
        }
      }
    }
  }
  
  if (buffer.trim()) {
    const parsed = JSON.parse(buffer);
    if (parsed.type === "final") {
      finalData = parsed.data;
    }
  }

  return finalData;
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
