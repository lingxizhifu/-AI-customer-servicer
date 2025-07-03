require('dotenv').config();
const nodemailer = require('nodemailer');

async function testEmailConnection() {
  console.log('🧪 开始测试邮箱配置...');
  
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT),
    secure: process.env.SMTP_PORT == 465,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS
    }
  });

  try {
    await transporter.verify();
    console.log('✅ 邮箱服务器连接成功！');
    
    const testEmail = {
      from: process.env.SMTP_USER,
      to: process.env.SMTP_USER,
      subject: '聆析智服 - 邮箱配置测试',
      html: `
        <h2>🎉 邮箱配置测试成功！</h2>
        <p>如果您收到这封邮件，说明邮箱配置正确。</p>
        <p>测试时间：${new Date().toLocaleString()}</p>
      `
    };
    
    await transporter.sendMail(testEmail);
    console.log('📧 测试邮件发送成功！请检查您的邮箱。');
    
  } catch (error) {
    console.error('❌ 邮箱配置测试失败:', error.message);
    console.error('请检查.env文件中的邮箱配置信息');
  }
}

testEmailConnection();