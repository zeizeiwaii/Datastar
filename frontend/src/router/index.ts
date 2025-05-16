import { createRouter, createWebHistory } from 'vue-router'
import UserRequest from '../views/UserRequest.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import ProxyTestView from '../views/ProxyTestView.vue'
import RoutePlanningView from '../views/RoutePlanningView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: UserRequest
        },
        {
            path: '/admin',
            name: 'admin',
            component: AdminDashboard
        },
        {
            path: '/proxy-test',
            name: 'proxy-test',
            component: ProxyTestView
        },
        {
            path: '/route-planning',
            name: 'route-planning',
            component: RoutePlanningView
        }
    ]
})

export default router 