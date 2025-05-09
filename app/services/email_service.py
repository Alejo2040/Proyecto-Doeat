import os
import smtplib
import logging
from email.message import EmailMessage
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailService:
    """
    Clase para gestionar el envío de correos electrónicos.
    """
    def __init__(self):
        """
        Inicializa el servicio de correo con configuración desde variables de entorno.
        """
        self.email_address = os.getenv("EMAIL_ADDRESS", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        if not self.email_address or not self.email_password:
            logger.warning("Credenciales de correo no configuradas correctamente")
 
    def send_verification_email(self, to_email: str, token: str) -> bool:
        """
        Envía un correo de verificación al usuario.
        
        Args:
            to_email (str): Dirección de correo del destinatario
            token (str): Token de verificación
            
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            verification_url = f"{self.base_url}/auth/verify/{token}"
            
            # Crear mensaje
            msg = EmailMessage()
            msg['Subject'] = "Verificación de Cuenta - Sistema de Inventario"
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            # Contenido del mensaje en formato HTML
            msg.set_content(
                f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #2a5885;">Verificación de Cuenta</h2>
                        <p>Gracias por registrarte en nuestro sistema de inventario. Para verificar tu cuenta, por favor haz clic en el siguiente enlace:</p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" style="display: inline-block; background-color: #2a5885; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verificar mi cuenta</a>
                        </p>
                        <p>Si no puedes hacer clic en el enlace, copia y pega la siguiente URL en tu navegador:</p>
                        <p style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; word-break: break-all;">{verification_url}</p>
                        <p>Si no has solicitado esta verificación, puedes ignorar este correo.</p>
                        <p>Saludos,<br>El equipo de Sistema de Inventario</p>
                    </div>
                </body>
                </html>
                """,
                subtype='html'
            )
            
            # Enviar correo
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                smtp.login(self.email_address, self.email_password)
                smtp.send_message(msg)
                
            logger.info(f"Correo de verificación enviado a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar correo de verificación: {str(e)}")
            return False
            
    def send_password_reset_email(self, to_email: str, token: str, username: str) -> bool:
        """
        Envía un correo para restablecer la contraseña.
        
        Args:
            to_email (str): Dirección de correo del destinatario
            token (str): Token de restablecimiento
            username (str): Nombre de usuario
            
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            reset_url = f"{self.base_url}/auth/reset-password/{token}"
            
            # Crear mensaje
            msg = EmailMessage()
            msg['Subject'] = "Restablecimiento de Contraseña - Sistema de Inventario"
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            # Contenido del mensaje en formato HTML
            msg.set_content(
                f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #2a5885;">Restablecimiento de Contraseña</h2>
                        <p>Hola {username},</p>
                        <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta. Si no fuiste tú quien la solicitó, puedes ignorar este correo.</p>
                        <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" style="display: inline-block; background-color: #2a5885; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Restablecer mi contraseña</a>
                        </p>
                        <p>Si no puedes hacer clic en el enlace, copia y pega la siguiente URL en tu navegador:</p>
                        <p style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; word-break: break-all;">{reset_url}</p>
                        <p>Este enlace expirará en 1 hora por motivos de seguridad.</p>
                        <p>Saludos,<br>El equipo de Sistema de Inventario</p>
                    </div>
                </body>
                </html>
                """,
                subtype='html'
            )
            
            # Enviar correo
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                smtp.login(self.email_address, self.email_password)
                smtp.send_message(msg)
                
            logger.info(f"Correo de restablecimiento de contraseña enviado a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar correo de restablecimiento: {str(e)}")
            return False
            
    def send_purchase_confirmation(self, to_email: str, purchase_data: dict) -> bool:
        """
        Envía una confirmación de compra.
        
        Args:
            to_email (str): Dirección de correo del destinatario
            purchase_data (dict): Datos de la compra
            
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            # Crear mensaje
            msg = EmailMessage()
            msg['Subject'] = f"Confirmación de Compra #{purchase_data['id']} - Sistema de Inventario"
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            # Generar tabla de productos
            items_table = ""
            for item in purchase_data['items']:
                items_table += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{item['product_name']}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{item['quantity']}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${item['unit_price']:.2f}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${item['subtotal']:.2f}</td>
                </tr>
                """
            
            # Contenido del mensaje en formato HTML
            msg.set_content(
                f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #2a5885;">Confirmación de Compra</h2>
                        <p>Se ha registrado la siguiente compra en el sistema:</p>
                        
                        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <p><strong>Compra ID:</strong> #{purchase_data['id']}</p>
                            <p><strong>Proveedor:</strong> {purchase_data['supplier_name']}</p>
                            <p><strong>Referencia:</strong> {purchase_data.get('reference', 'N/A')}</p>
                            <p><strong>Fecha:</strong> {purchase_data['created_at'].strftime('%d/%m/%Y %H:%M')}</p>
                        </div>
                        
                        <h3>Detalle de productos:</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background-color: #2a5885; color: white;">
                                    <th style="padding: 10px; text-align: left;">Producto</th>
                                    <th style="padding: 10px; text-align: center;">Cantidad</th>
                                    <th style="padding: 10px; text-align: right;">Precio Unit.</th>
                                    <th style="padding: 10px; text-align: right;">Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_table}
                            </tbody>
                            <tfoot>
                                <tr style="font-weight: bold;">
                                    <td colspan="3" style="padding: 10px; text-align: right;">Total:</td>
                                    <td style="padding: 10px; text-align: right;">${purchase_data['total_amount']:.2f}</td>
                                </tr>
                            </tfoot>
                        </table>
                        
                        <p>Saludos,<br>El equipo de Sistema de Inventario</p>
                    </div>
                </body>
                </html>
                """,
                subtype='html'
            )
            
            # Enviar correo
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                smtp.login(self.email_address, self.email_password)
                smtp.send_message(msg)
                
            logger.info(f"Confirmación de compra enviada a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar confirmación de compra: {str(e)}")
            return False