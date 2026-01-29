<template>
  <div class="help-panel" :class="{ 'is-open': isOpen }">
    <!-- 帮助按钮 -->
    <button
      class="help-button"
      @click="toggle"
      :title="isOpen ? '关闭帮助' : '打开帮助'"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <span class="badge">?</span>
    </button>

    <!-- 帮助面板 -->
    <div class="panel-content" v-show="isOpen">
      <div class="panel-header">
        <h3>📚 操作指引</h3>
        <button class="close-btn" @click="toggle">✕</button>
      </div>

      <div class="panel-body">
        <!-- 快速链接 -->
        <div class="quick-links">
          <h4>快速开始</h4>
          <ul>
            <li><a href="#demo" @click="showSection('demo')">🎯 查看Demo项目</a></li>
            <li><a href="#create" @click="showSection('create')">✨ 创建新项目</a></li>
            <li><a href="#config" @click="showSection('config')">⚙️ 配置AI模型</a></li>
            <li><a href="#workflow" @click="showSection('workflow')">🚀 执行工作流</a></li>
          </ul>
        </div>

        <!-- 当前页面帮助 -->
        <div class="current-page-help">
          <h4>{{ currentPageTitle }}</h4>
          <div class="help-content" v-html="currentHelpContent"></div>
        </div>

        <!-- 常见问题 -->
        <div class="faq">
          <h4>常见问题</h4>
          <div class="faq-item" v-for="(faq, index) in currentFAQs" :key="index">
            <div class="faq-question" @click="toggleFAQ(index)">
              {{ faq.question }}
              <span class="toggle-icon">{{ faq.open ? '▼' : '▶' }}</span>
            </div>
            <div class="faq-answer" v-show="faq.open">
              {{ faq.answer }}
            </div>
          </div>
        </div>

        <!-- 提示 -->
        <div class="tips" v-if="currentTips.length > 0">
          <h4>💡 提示</h4>
          <ul>
            <li v-for="(tip, index) in currentTips" :key="index">{{ tip }}</li>
          </ul>
        </div>
      </div>

      <!-- 底部链接 -->
      <div class="panel-footer">
        <a href="/docs" target="_blank">📖 查看完整文档</a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HelpPanel',
  data() {
    return {
      isOpen: false,
      helpData: {
        project: {
          title: '项目管理帮助',
          content: `
            <p><strong>项目列表</strong>显示您创建的所有AI故事项目。</p>
            <p><strong>状态说明：</strong></p>
            <ul>
              <li>📝 <strong>draft</strong> - 草稿状态，可以编辑和执行</li>
              <li>⏳ <strong>processing</strong> - 处理中，AI正在生成</li>
              <li>✅ <strong>completed</strong> - 已完成</li>
              <li>❌ <strong>failed</strong> - 执行失败</li>
            </ul>
          `,
          faqs: [
            {
              question: '如何创建新项目？',
              answer: '点击右上角的"创建项目"按钮，输入项目主题，选择提示词模板和AI模型，然后点击"创建"即可。',
              open: false
            },
            {
              question: '项目执行失败怎么办？',
              answer: '1. 检查AI模型配置是否正确\n2. 查看项目详情页的错误信息\n3. 确认Celery Worker正在运行\n4. 查看浏览器控制台的错误日志',
              open: false
            },
            {
              question: '如何删除项目？',
              answer: '在项目列表中点击项目卡片的"删除"按钮，确认后即可删除。注意：删除后无法恢复。',
              open: false
            }
          ],
          tips: [
            '首次使用建议先查看Demo项目',
            '使用Mock AI可以快速测试，无需API密钥',
            '项目会自动保存所有阶段的输出结果'
          ]
        },
        'project-create': {
          title: '创建项目帮助',
          content: `
            <p><strong>创建项目</strong>是AI视频生成的第一步。</p>
            <p><strong>必填字段：</strong></p>
            <ul>
              <li><strong>项目名称</strong> - 给项目起个名字</li>
              <li><strong>原始主题</strong> - 描述您想创作的内容</li>
            </ul>
            <p><strong>可选配置：</strong></p>
            <ul>
              <li><strong>提示词模板集</strong> - 选择预定义的AI指令模板</li>
              <li><strong>AI模型</strong> - 选择LLM、图片生成、视频生成模型</li>
            </ul>
          `,
          faqs: [
            {
              question: '如何填写原始主题？',
              answer: '详细描述您想要创作的内容，例如："宁静的小镇，清晨的阳光洒在石板路上，年轻的画家在溪边写生，远处的山峦若隐若现"。描述越详细，生成效果越好。',
              open: false
            },
            {
              question: '提示词模板集是必须的吗？',
              answer: '不是必须的。如果不选择，系统会使用默认模板。建议选择"Demo完整模板集"以获得最佳效果。',
              open: false
            },
            {
              question: '如何选择AI模型？',
              answer: '如果是快速测试，选择"Demo Mock"即可。如需真实输出，需要先配置AI Provider（在"模型管理"页面），然后在这里选择。',
              open: false
            }
          ],
          tips: [
            '项目主题建议50-200字',
            '可以使用Demo模板集快速开始',
            '创建后可以在详情页修改配置'
          ]
        },
        model: {
          title: '模型管理帮助',
          content: `
            <p><strong>AI模型管理</strong>用于配置不同的AI服务提供商。</p>
            <p><strong>支持3种模型类型：</strong></p>
            <ul>
              <li>🤖 <strong>LLM</strong> - 大语言模型（OpenAI GPT-4、Claude等）</li>
              <li>🎨 <strong>Text2Image</strong> - 文生图模型（Stable Diffusion、DALL-E）</li>
              <li>🎬 <strong>Image2Video</strong> - 图生视频模型（Runway Gen-2）</li>
            </ul>
          `,
          faqs: [
            {
              question: '如何快速开始？',
              answer: '系统已自动创建了3个Demo Mock Provider，直接使用即可。Mock AI会返回模拟数据，速度很快，适合测试。',
              open: false
            },
            {
              question: '如何配置真实的OpenAI API？',
              answer: '1. 在OpenAI获取API密钥\n2. 点击"添加提供商"\n3. 选择类型"LLM"\n4. 填写名称"OpenAI GPT-4"\n5. 填写API URL: https://api.openai.com/v1\n6. 填写API密钥\n7. 保存即可',
              open: false
            }
          ],
          tips: [
            '使用Mock AI可以免费测试',
            '配置真实AI需要API密钥',
            '建议先用Mock测试流程，再配置真实AI'
          ]
        },
        prompt: {
          title: '提示词管理帮助',
          content: `
            <p><strong>提示词模板</strong>是控制AI生成质量的核心。</p>
            <p><strong>模板语法：</strong></p>
            <ul>
              <li>使用Jinja2模板语法</li>
              <li>变量用双花括号包围：{{ variable_name }}</li>
              <li>系统会自动替换变量为实际内容</li>
            </ul>
          `,
          faqs: [
            {
              question: '如何创建提示词模板？',
              answer: '1. 创建"提示词集"（一组相关的模板）\n2. 在提示词集中添加各个阶段的模板\n3. 使用Jinja2语法引用变量\n4. 保存后在创建项目时选择',
              open: false
            },
            {
              question: '可用的变量有哪些？',
              answer: 'Rewrite阶段：{{ raw_text }}\nStoryboard阶段：{{ rewritten_text }}\nImage阶段：{{ scene_description }}, {{ camera_angle }}\nCamera阶段：{{ scene_description }}\nVideo阶段：{{ image_urls }}, {{ camera_movements }}',
              open: false
            }
          ],
          tips: [
            'Demo模板集提供了完整的示例',
            '提示词越详细，生成效果越好',
            '可以参考Demo模板编写自己的提示词'
          ]
        }
      }
    };
  },
  computed: {
    currentPage() {
      const path = this.$route.path;
      if (path.includes('/projects')) {
        return 'project';
      } else if (path.includes('/create')) {
        return 'project-create';
      } else if (path.includes('/models')) {
        return 'model';
      } else if (path.includes('/prompts')) {
        return 'prompt';
      }
      return 'project';
    },
    currentPageTitle() {
      return this.helpData[this.currentPage]?.title || '帮助';
    },
    currentHelpContent() {
      return this.helpData[this.currentPage]?.content || '<p>暂无帮助信息</p>';
    },
    currentFAQs() {
      return this.helpData[this.currentPage]?.faqs || [];
    },
    currentTips() {
      return this.helpData[this.currentPage]?.tips || [];
    }
  },
  methods: {
    toggle() {
      this.isOpen = !this.isOpen;
    },
    toggleFAQ(index) {
      this.currentFAQs[index].open = !this.currentFAQs[index].open;
    },
    showSection(section) {
      // 跳转到指定部分
      console.log('Show section:', section);
    }
  }
};
</script>

<style scoped>
.help-panel {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1000;
}

.help-button {
  position: absolute;
  right: 100%;
  top: 0;
  width: 50px;
  height: 50px;
  border-radius: 25px 0 0 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: -2px 0 8px rgba(0,0,0,0.2);
  transition: all 0.3s;
}

.help-button:hover {
  width: 60px;
}

.badge {
  position: absolute;
  top: 5px;
  right: 5px;
  background: #ffd700;
  color: #333;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 14px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-content {
  width: 350px;
  max-height: 80vh;
  background: white;
  border-radius: 8px 0 0 8px;
  box-shadow: -4px 0 16px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.panel-header {
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255,255,255,0.2);
}

.panel-body {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.quick-links h4,
.current-page-help h4,
.faq h4,
.tips h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.quick-links ul {
  list-style: none;
  padding: 0;
  margin: 0 0 16px 0;
}

.quick-links li {
  margin-bottom: 8px;
}

.quick-links a {
  color: #667eea;
  text-decoration: none;
  display: block;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.quick-links a:hover {
  background: #f0f0ff;
}

.current-page-help {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.help-content {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.help-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.help-content li {
  margin-bottom: 4px;
}

.faq {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.faq-item {
  margin-bottom: 8px;
}

.faq-question {
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.2s;
}

.faq-question:hover {
  background: #f0f0ff;
}

.toggle-icon {
  font-size: 12px;
  color: #999;
}

.faq-answer {
  padding: 10px;
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  background: #fafafa;
  border-radius: 4px;
  margin-top: 4px;
  white-space: pre-line;
}

.tips ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tips li {
  padding: 8px 12px;
  background: #fff9e6;
  border-left: 3px solid #ffd700;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
}

.panel-footer {
  padding: 12px 16px;
  background: #f9f9f9;
  border-top: 1px solid #eee;
}

.panel-footer a {
  color: #667eea;
  text-decoration: none;
  font-size: 13px;
  display: block;
  text-align: center;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.panel-footer a:hover {
  background: #f0f0ff;
}
</style>
