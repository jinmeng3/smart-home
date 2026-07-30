import { createApp } from "vue";
import { createPinia } from "pinia";
import { ElBadge, ElButton, ElInput, ElSwitch } from "element-plus";
import App from "./App.vue";
import { router } from "./router";
import "element-plus/theme-chalk/base.css";
import "element-plus/theme-chalk/el-badge.css";
import "element-plus/theme-chalk/el-button.css";
import "element-plus/theme-chalk/el-input.css";
import "element-plus/theme-chalk/el-switch.css";
import "./styles/main.css";

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(ElBadge);
app.use(ElButton);
app.use(ElInput);
app.use(ElSwitch);
app.mount("#app");
