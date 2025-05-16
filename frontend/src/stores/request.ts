import { defineStore } from 'pinia'
import type { Request } from '@/types/request'

interface RequestState {
    requests: Request[];
    loading: boolean;
    error: string | null;
}

export const useRequestStore = defineStore('request', {
    state: (): RequestState => ({
        requests: [],
        loading: false,
        error: null
    }),

    actions: {
        async fetchRequests() {
            this.loading = true
            try {
                // TODO: 实现API调用
                this.requests = []
                this.error = null
            } catch (error) {
                this.error = error instanceof Error ? error.message : '获取请求列表失败'
            } finally {
                this.loading = false
            }
        },

        async submitRequest(request: Omit<Request, 'id' | 'status' | 'createdAt' | 'updatedAt'>) {
            this.loading = true
            try {
                // TODO: 实现API调用
                this.error = null
            } catch (error) {
                this.error = error instanceof Error ? error.message : '提交请求失败'
                throw error
            } finally {
                this.loading = false
            }
        }
    }
}) 