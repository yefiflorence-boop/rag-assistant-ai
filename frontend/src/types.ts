export interface Source {
  name: string;
  page: string;
  url: string;
  label: string;
}

export type Role = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  time: string;
  sources: Source[];
  refusal?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  messages: ChatMessage[];
}

export type Theme = 'sombre' | 'clair';

export interface Manifest {
  date_indexation?: string;
  nb_documents?: number;
  nb_chunks?: number;
  embedding_model?: string;
}

export interface DocItem {
  name: string;
  size: number;
  url: string;
}

export interface DrhContact {
  nom: string;
  email: string;
  tel: string;
  horaires: string;
}

export interface ChatDone {
  answer: string;
  sources: Source[];
  refusal: boolean;
}
