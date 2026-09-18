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
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/ForgotPasswordView.vue'),
      meta: { guest: true },
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('@/views/ResetPasswordView.vue'),
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
        { path: '', redirect: () => ({ name: firstAccessibleAdminRoute() }) },
        {
          path: 'metrics',
          name: 'admin-metrics',
          component: () => import('@/views/admin/AdminMetricsView.vue'),
          meta: { permission: 'metrics' },
        },
        {
          path: 'messages',
          name: 'admin-messages',
          component: () => import('@/views/admin/AdminMessagesView.vue'),
          meta: { permission: 'messages' },
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('@/views/admin/AdminUsersView.vue'),
          meta: { permission: 'users' },
        },
        {
          path: 'roles',
          name: 'admin-roles',
          component: () => import('@/views/admin/AdminRolesView.vue'),
          meta: { permission: 'roles' },
        },
        {
          path: 'limits',
          name: 'admin-limits',
          component: () => import('@/views/admin/AdminLimitsView.vue'),
          meta: { permission: 'limits' },
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

const ADMIN_TABS_ORDER = ['metrics', 'messages', 'users', 'roles', 'limits']

function firstAccessibleAdminRoute(): string {
  const auth = useAuthStore()
  if (auth.isAdmin) return 'admin-metrics'
  const first = ADMIN_TABS_ORDER.find((key) => auth.hasPermission(key))
  return first ? `admin-${first}` : 'messages'
}

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !auth.canAccessAdmin) {
    return { name: 'messages' }
  }
  if (typeof to.meta.permission === 'string' && !auth.hasPermission(to.meta.permission)) {
    return { name: firstAccessibleAdminRoute() }
  }
  if (to.meta.guest && auth.isAuthenticated) {
    return { name: 'messages' }
  }
  return true
})

export default router
