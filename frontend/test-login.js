const { chromium } = require('playwright');

(async () => {
  console.log('Launching browser...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });

  const page = await context.newPage();

  console.log('Navigating to frontend...');
  await page.goto('http://10.30.5.62:3000', { waitUntil: 'networkidle' });

  console.log('Page title:', await page.title());
  console.log('Current URL:', page.url());

  // Take screenshot before login
  await page.screenshot({ path: '/tmp/login-page.png' });
  console.log('Screenshot saved to /tmp/login-page.png');

  // Fill in login form
  console.log('Filling login form...');
  try {
    // Wait for Vue app to render
    await page.waitForSelector('input[placeholder*="用户名"]', { timeout: 10000 });
    await page.fill('input[placeholder*="用户名"]', 'pwl1987');
    await page.fill('input[placeholder*="密码"]', 'Ilinyi@2024');

    // Click login button (find by text "登录")
    await page.click('button:has-text("登录")');

    console.log('Login button clicked, waiting for response...');
    await page.waitForTimeout(5000);

    // Check result
    const currentUrl = page.url();
    console.log('Current URL after login:', currentUrl);

    // Take screenshot after login attempt
    await page.screenshot({ path: '/tmp/after-login.png', fullPage: true });
    console.log('Screenshot saved to /tmp/after-login.png');

    // Get page content for debugging
    const content = await page.content();
    console.log('Page contains "pwl1987":', content.includes('pwl1987'));

    // Check for common success indicators
    const hasLogout = content.includes('退出') || content.includes('登出') || content.includes('注销');
    const hasUser = content.includes('pwl1987');
    const hasError = content.includes('错误') || content.includes('失败') || content.includes('用户名或密码');

    if (hasLogout || hasUser) {
      console.log('SUCCESS: Login appears to be successful!');
    } else if (hasError) {
      console.log('WARNING: Login may have failed - error indicators found');
    } else {
      console.log('INFO: Unable to determine login status from page content');
      console.log('Current URL:', currentUrl);
    }
  } catch (e) {
    console.log('Error during login:', e.message);
    // Take screenshot of error state
    await page.screenshot({ path: '/tmp/error-state.png' });
    console.log('Error screenshot saved to /tmp/error-state.png');
  }

  await browser.close();
  console.log('Browser closed');
})();
