import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'messages',
      component: () => import('@/views/MessagesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        { path: '', redirect: { name: 'admin-metrics' } },
        {
          path: 'metrics',
          name: 'admin-metrics',
          component: () => import('@/views/admin/AdminMetricsView.vue'),
        },
        {
          path: 'messages',
          name: 'admin-messages',
          component: () => import('@/views/admin/AdminMessagesView.vue'),
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('@/views/admin/AdminUsersView.vue'),
        },
        {
          path: 'roles',
          name: 'admin-roles',
          component: () => import('@/views/admin/AdminRolesView.vue'),
        },
        {
          path: 'limits',
          name: 'admin-limits',
          component: () => import('@/views/admin/AdminLimitsView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'messages' }
  }
  if (to.meta.guest && auth.isAuthenticated) {
    return { name: 'messages' }
  }
  return true
})

export default router
