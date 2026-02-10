const { chromium } = require('playwright');

(async () => {
  console.log('=== 局域网登录测试 ===\n');
  
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();
  
  // 监听网络请求
  page.on('request', request => {
    if (request.url().includes('/login/')) {
      console.log('📤 请求:', request.method(), request.url());
      console.log('   Headers:', JSON.stringify(request.headers(), null, 2));
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/login/')) {
      console.log('📥 响应:', response.status(), response.url());
      response.text().then(text => {
        const data = JSON.parse(text);
        console.log('   Body:', JSON.stringify(data, null, 2));
      }).catch(() => {});
    }
  });

  console.log('1. 导航到登录页面...');
  await page.goto('http://10.30.5.62:3000/login', { waitUntil: 'networkidle' });
  console.log('   ✅ 页面加载完成:', page.url());

  console.log('\n2. 填写登录表单...');
  await page.fill('input[placeholder*="用户名"]', 'pwl1987');
  await page.fill('input[placeholder*="密码"]', 'Ilinyi@2024');
  console.log('   ✅ 表单填写完成');

  console.log('\n3. 提交登录...');
  await page.click('button:has-text("登录")');
  
  console.log('\n4. 等待响应...');
  await page.waitForTimeout(5000);

  const currentUrl = page.url();
  console.log('\n5. 最终 URL:', currentUrl);
  
  if (currentUrl.includes('/projects')) {
    console.log('   ✅ 登录成功！已跳转到项目页面');
  } else {
    console.log('   ❌ 登录可能失败');
  }

  // 获取页面内容
  const hasUser = await page.textContent('body').then(text => text.includes('pwl1987'));
  console.log('   页面包含用户信息:', hasUser ? '✅ 是' : '❌ 否');

  await browser.close();
  console.log('\n=== 测试完成 ===');
})();
