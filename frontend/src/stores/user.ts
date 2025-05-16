import { defineStore } from 'pinia'

interface UserState {
    id: number | null;
    username: string;
    isLoggedIn: boolean;
}

export const useUserStore = defineStore('user', {
    state: (): UserState => ({
        id: null,
        username: '',
        isLoggedIn: false
    }),

    actions: {
        setUser(user: { id: number; username: string }) {
            this.id = user.id
            this.username = user.username
            this.isLoggedIn = true
        },

        clearUser() {
            this.id = null
            this.username = ''
            this.isLoggedIn = false
        }
    }
}) 