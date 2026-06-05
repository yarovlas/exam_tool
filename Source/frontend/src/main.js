import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/tokens.css'
import './styles/global.css'
import './styles/buttons.css'
import './styles/forms.css'
import './styles/cards.css'
import './styles/master-detail.css'
import './styles/login.css'
import './styles/dashboard.css'

createApp(App).use(router).mount('#app')
