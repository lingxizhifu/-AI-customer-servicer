# 文件路径：customer_service/management/commands/create_test_faqs.py
# 基于你的实际FAQ模型定义

from django.core.management.base import BaseCommand
from customer_service.models import FAQ

class Command(BaseCommand):
    help = '创建测试FAQ数据'

    def handle(self, *args, **options):
        # 清除现有的测试数据
        self.stdout.write('正在清除现有FAQ数据...')
        FAQ.objects.all().delete()
        
        # 创建测试FAQ数据 - 只使用模型中存在的字段
        test_faqs = [
            {
                'question': '如何注册账户？',
                'answer': '您可以点击页面右上角的"注册"按钮，填写相关信息即可完成注册。注册需要提供有效的邮箱地址和手机号码。',
                'category': '注册问题',
                'is_main': True
            },
            {
                'question': '忘记密码怎么办？',
                'answer': '在登录页面点击"忘记密码"，输入您的邮箱地址，系统会发送重置密码的链接到您的邮箱。',
                'category': '账户问题',
                'is_main': True
            },
            {
                'question': '支持哪些支付方式？',
                'answer': '我们支持支付宝、微信支付、银行卡支付等多种支付方式。具体支付方式会在结算页面显示。',
                'category': '支付问题',
                'is_main': True
            },
            {
                'question': '如何申请退款？',
                'answer': '您可以在订单页面找到相应订单，点击"申请退款"按钮。退款申请会在3-5个工作日内处理完成。',
                'category': '支付问题',
                'is_main': True
            },
            {
                'question': '网站打不开怎么办？',
                'answer': '请检查您的网络连接，尝试刷新页面或清除浏览器缓存。如果问题持续存在，请联系客服。',
                'category': '技术问题',
                'is_main': True
            },
            {
                'question': '如何修改个人信息？',
                'answer': '登录后进入"个人中心"，在"个人资料"页面可以修改您的基本信息，包括姓名、手机号等。',
                'category': '账户问题',
                'is_main': True
            },
            {
                'question': '客服工作时间是什么时候？',
                'answer': '我们的客服工作时间是周一至周日，上午9:00-12:00，下午14:00-18:00。',
                'category': '其他问题',
                'is_main': True
            },
            {
                'question': '如何联系客服？',
                'answer': '您可以通过在线客服、客服热线400-888-8888或邮箱service@example.com联系我们。',
                'category': '其他问题',
                'is_main': True
            },
            {
                'question': '账户被锁定了怎么办？',
                'answer': '如果您的账户被锁定，请联系客服处理。通常是由于多次输入错误密码导致，24小时后会自动解锁。',
                'category': '账户问题',
                'is_main': False  # 这个设为禁用状态作为测试
            },
            {
                'question': '商品质量有问题如何处理？',
                'answer': '如果收到的商品有质量问题，请在收货后7天内联系客服，我们会为您安排退换货服务。',
                'category': '其他问题',
                'is_main': True
            },
            {
                'question': '订单配送需要多长时间？',
                'answer': '一般情况下，订单会在24小时内发货，配送时间根据地区不同，通常为1-3个工作日。',
                'category': '其他问题',
                'is_main': True
            },
            {
                'question': '如何查看订单状态？',
                'answer': '登录后在"我的订单"页面可以查看所有订单的详细状态，包括待付款、待发货、配送中等。',
                'category': '其他问题',
                'is_main': True
            },
            {
                'question': '新用户有什么优惠？',
                'answer': '新用户注册即可获得50元优惠券，首次购买满100元可使用。详细活动信息请查看活动页面。',
                'category': '注册问题',
                'is_main': True
            },
            {
                'question': '会员等级有什么好处？',
                'answer': '不同等级的会员可享受不同的折扣优惠、专属客服、生日礼品等特权。具体权益请查看会员中心。',
                'category': '账户问题',
                'is_main': True
            },
            {
                'question': '手机验证码收不到怎么办？',
                'answer': '请检查手机号是否正确，确认手机信号良好。如果仍收不到，可以尝试语音验证码或联系客服。',
                'category': '技术问题',
                'is_main': True
            },
            {
                'question': '如何取消订单？',
                'answer': '在订单页面找到相应订单，如果订单状态为"待发货"，您可以点击"取消订单"按钮进行取消。',
                'category': '其他问题',
                'is_main': True
            },
            {
                'question': '积分如何使用？',
                'answer': '积分可以在购买商品时抵扣现金，通常100积分=1元。具体使用规则请查看积分商城。',
                'category': '账户问题',
                'is_main': True
            },
            {
                'question': '如何更换绑定手机号？',
                'answer': '进入个人中心-安全设置，验证当前手机号后可以绑定新的手机号码。',
                'category': '账户问题',
                'is_main': True
            },
            {
                'question': '商品可以开发票吗？',
                'answer': '可以的，在下单时选择"需要发票"，填写发票信息即可。我们支持电子发票和纸质发票。',
                'category': '其他问题',
                'is_main': True
            },
            {
                'question': '如何查看物流信息？',
                'answer': '在订单详情页面可以查看物流跟踪信息，也可以通过物流公司官网或电话查询。',
                'category': '其他问题',
                'is_main': True
            }
        ]
        
        created_count = 0
        for faq_data in test_faqs:
            try:
                # 直接创建FAQ对象，created_at和updated_at会自动设置
                faq = FAQ.objects.create(
                    question=faq_data['question'],
                    answer=faq_data['answer'],
                    category=faq_data['category'],
                    is_main=faq_data['is_main']
                )
                created_count += 1
                self.stdout.write(f'创建FAQ: {faq.question}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'创建FAQ失败: {faq_data["question"]} - {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'成功创建 {created_count} 条测试FAQ数据')
        )
        self.stdout.write(
            self.style.SUCCESS(f'总共有 {FAQ.objects.count()} 条FAQ数据')
        )