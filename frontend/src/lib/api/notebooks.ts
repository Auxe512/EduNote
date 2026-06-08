import apiClient from './client'
import {
  NotebookResponse,
  CreateNotebookRequest,
  UpdateNotebookRequest,
  NotebookDeletePreview,
  NotebookDeleteResponse,
} from '@/lib/types/api'

// EduNote: notebooks are scoped per student. The current student's id lives in
// localStorage (set on the "輸入名字" gate); inject it as `owner` so each student
// only lists/creates their own notebooks. Returns undefined before a name is set.
function currentStudentId(): string | undefined {
  if (typeof window === 'undefined') return undefined
  return localStorage.getItem('edunote:student_id') ?? undefined
}

export const notebooksApi = {
  list: async (params?: { archived?: boolean; order_by?: string }) => {
    const response = await apiClient.get<NotebookResponse[]>('/notebooks', {
      params: { ...params, owner: currentStudentId() },
    })
    return response.data
  },

  get: async (id: string) => {
    const response = await apiClient.get<NotebookResponse>(`/notebooks/${id}`)
    return response.data
  },

  create: async (data: CreateNotebookRequest) => {
    const response = await apiClient.post<NotebookResponse>('/notebooks', {
      ...data,
      owner: currentStudentId(),
    })
    return response.data
  },

  update: async (id: string, data: UpdateNotebookRequest) => {
    const response = await apiClient.put<NotebookResponse>(`/notebooks/${id}`, data)
    return response.data
  },

  deletePreview: async (id: string) => {
    const response = await apiClient.get<NotebookDeletePreview>(
      `/notebooks/${id}/delete-preview`
    )
    return response.data
  },

  delete: async (id: string, deleteExclusiveSources: boolean = false) => {
    const response = await apiClient.delete<NotebookDeleteResponse>(`/notebooks/${id}`, {
      params: { delete_exclusive_sources: deleteExclusiveSources },
    })
    return response.data
  },

  addSource: async (notebookId: string, sourceId: string) => {
    const response = await apiClient.post(`/notebooks/${notebookId}/sources/${sourceId}`)
    return response.data
  },

  removeSource: async (notebookId: string, sourceId: string) => {
    const response = await apiClient.delete(`/notebooks/${notebookId}/sources/${sourceId}`)
    return response.data
  },
}