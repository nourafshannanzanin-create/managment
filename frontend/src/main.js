import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './tailwind.css'
import './styles.css'
import './styles/jade-enterprise.css'
import './styles/layout-core.css'
import './styles/mobile-ui.css'

createApp(App).use(router).mount('#app')
