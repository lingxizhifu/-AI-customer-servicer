require('dotenv').config();
const express = require('express');
const nodemailer = require('nodemailer');
const cors = require('cors');
const crypto = require('crypto');
const rateLimit = require('express-rate-limit');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件配置
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? ['https://your-domain.com'] 
    : ['http://localhost:3000', 'http://127.0.0.1:3000'],
  credentials: true
}));

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 速率限制
const emailLimiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW) || 15 * 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_MAX) || 5,
  message: {
    success: false,
    message: '请求过于频繁，请稍后再试'
  },
  standardHeaders: true,
  legacyHeaders: false
});

// 内存存储验证码（生产环境建议使用Redis）
const verificationCodes = new Map();

// 邮箱配置验证
function validateEmailConfig() {
  const required = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS'];
  const missing = required.filter(key => !process.env[key]);
  
  if (missing.length > 0) {
    console.error('❌ 缺少必要的环境变量:', missing.join(', '));
    console.error('请检查.env文件配置');
    process.exit(1);
  }
}

validateEmailConfig();

// 创建邮件传输器
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: parseInt(process.env.SMTP_PORT),
  secure: process.env.SMTP_PORT == 465,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  },
  // 调试选项
  debug: process.env.NODE_ENV === 'development',
  logger: process.env.NODE_ENV === 'development'
});

// 验证邮箱配置
transporter.verify((error, success) => {
  if (error) {
    console.error('❌ 邮箱配置验证失败:', error.message);
    console.error('请检查.env文件中的邮箱配置');
  } else {
    console.log('✅ 邮箱服务器连接成功');
  }
});

// 工具函数
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

function generateVerificationCode() {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

// 发送验证码接口
app.post('/api/send-verification-code', emailLimiter, async (req, res) => {
  try {
    const { email, type = 'bind' } = req.body;
    
    if (!email || !isValidEmail(email)) {
      return res.status(400).json({
        success: false,
        message: '请输入有效的邮箱地址'
      });
    }
    
    const verificationCode = generateVerificationCode();
    const timestamp = Date.now();
    const key = `${email}_${type}`;
    
    // 存储验证码
    verificationCodes.set(key, {
      code: verificationCode,
      timestamp: timestamp,
      attempts: 0
    });
    
    // 5分钟后自动删除
    setTimeout(() => {
      verificationCodes.delete(key);
    }, 5 * 60 * 1000);
    
    // 邮件HTML模板
    const emailTemplate = `
      <div style="max-width: 600px; margin: 0 auto; font-family: 'Microsoft YaHei', Arial, sans-serif;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center; border-radius: 10px 10px 0 0;">
          <div style="background: rgba(255,255,255,0.2); width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 36px; color: white; font-weight: bold;">AI</div>
          <h1 style="color: white; margin: 0; font-size: 28px;">聆析智服</h1>
          <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">您的智能客服助手</p>
        </div>
        
        <div style="background: white; padding: 40px; border-radius: 0 0 10px 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.1);">
          <h2 style="color: #333; margin-bottom: 20px; font-size: 24px;">邮箱验证码</h2>
          <p style="color: #666; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
            您好！您正在进行邮箱${type === 'bind' ? '绑定' : '验证'}操作，请使用以下验证码完成验证：
          </p>
          
          <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 30px; border-radius: 10px; text-align: center; margin: 30px 0;">
            <div style="font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 8px; font-family: 'Courier New', monospace;">${verificationCode}</div>
            <p style="color: #999; margin: 15px 0 0 0; font-size: 14px;">验证码有效期为5分钟</p>
          </div>
          
          <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 30px 0;">
            <h3 style="color: #856404; margin: 0 0 10px 0; font-size: 16px;">⚠️ 安全提醒</h3>
            <ul style="color: #856404; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6;">
              <li>请勿将验证码泄露给他人</li>
              <li>验证码仅用于本次操作，请在5分钟内使用</li>
              <li>如非本人操作，请忽略此邮件</li>
            </ul>
          </div>
          
          <div style="border-top: 1px solid #eee; padding-top: 30px; margin-top: 40px; text-align: center;">
            <p style="color: #999; font-size: 14px; margin: 0;">
              此邮件由系统自动发送，请勿回复<br/>
              如有疑问，请联系客服
            </p>
            <p style="color: #ccc; font-size: 12px; margin: 15px 0 0 0;">
              © 2024 聆析智服. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    `;
    
    const mailOptions = {
      from: {
        name: '聆析智服',
        address: process.env.SMTP_USER
      },
      to: email,
      subject: '聆析智服 - 邮箱验证码',
      html: emailTemplate
    };
    
    await transporter.sendMail(mailOptions);
    
    res.json({
      success: true,
      message: '验证码已发送到您的邮箱，请注意查收',
      data: {
        email: email,
        expiresIn: 300
      }
    });
    
    console.log(`✅ 验证码已发送到 ${email}: ${verificationCode}`);
    
  } catch (error) {
    console.error('❌ 发送邮件失败:', error);
    res.status(500).json({
      success: false,
      message: '发送验证码失败，请稍后重试'
    });
  }
});

// 验证验证码接口
app.post('/api/verify-code', async (req, res) => {
  try {
    const { email, code, type = 'bind' } = req.body;
    
    if (!email || !code) {
      return res.status(400).json({
        success: false,
        message: '邮箱和验证码不能为空'
      });
    }
    
    const key = `${email}_${type}`;
    const storedData = verificationCodes.get(key);
    
    if (!storedData) {
      return res.status(400).json({
        success: false,
        message: '验证码已过期，请重新获取'
      });
    }
    
    if (storedData.attempts >= 3) {
      verificationCodes.delete(key);
      return res.status(400).json({
        success: false,
        message: '验证次数过多，请重新获取验证码'
      });
    }
    
    if (storedData.code !== code) {
      storedData.attempts++;
      return res.status(400).json({
        success: false,
        message: `验证码错误，还可尝试 ${3 - storedData.attempts} 次`
      });
    }
    
    const now = Date.now();
    const timeDiff = now - storedData.timestamp;
    if (timeDiff > 5 * 60 * 1000) {
      verificationCodes.delete(key);
      return res.status(400).json({
        success: false,
        message: '验证码已过期，请重新获取'
      });
    }
    
    verificationCodes.delete(key);
    
    res.json({
      success: true,
      message: '验证码验证成功',
      data: {
        email: email,
        verified: true,
        timestamp: now
      }
    });
    
    console.log(`✅ 邮箱 ${email} 验证成功`);
    
  } catch (error) {
    console.error('❌ 验证失败:', error);
    res.status(500).json({
      success: false,
      message: '验证失败，请稍后重试'
    });
  }
});

// 获取验证码状态
app.get('/api/verification-status/:email', (req, res) => {
  const { email } = req.params;
  const { type = 'bind' } = req.query;
  const key = `${email}_${type}`;
  const storedData = verificationCodes.get(key);
  
  if (!storedData) {
    return res.json({
      success: true,
      data: { exists: false, remainingTime: 0 }
    });
  }
  
  const now = Date.now();
  const timeDiff = now - storedData.timestamp;
  const remainingTime = Math.max(0, 5 * 60 * 1000 - timeDiff);
  
  res.json({
    success: true,
    data: {
      exists: true,
      remainingTime: Math.ceil(remainingTime / 1000),
      attempts: storedData.attempts
    }
  });
});

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    message: '服务运行正常',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// 首页路由
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 错误处理
app.use((error, req, res, next) => {
  console.error('❌ 服务器错误:', error);
  res.status(500).json({
    success: false,
    message: '服务器内部错误'
  });
});

// 404处理
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: '接口不存在'
  });
});

// 启动服务器
const server = app.listen(PORT, () => {
  console.log('🚀 聆析智服邮箱验证系统启动成功！');
  console.log(`📱 访问地址: http://localhost:${PORT}`);
  console.log(`🔗 API文档: http://localhost:${PORT}/api/health`);
  console.log('📧 请确保已正确配置.env文件中的邮箱信息');
});

// 优雅关闭
process.on('SIGTERM', () => {
  console.log('📴 收到终止信号，正在关闭服务器...');
  server.close(() => {
    console.log('✅ 服务器已关闭');
    process.exit(0);
  });
});

process.on('uncaughtException', (error) => {
  console.error('❌ 未捕获的异常:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ 未处理的Promise拒绝:', reason);
  process.exit(1);
});

module.exports = app;