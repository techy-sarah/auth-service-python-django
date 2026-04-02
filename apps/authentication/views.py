from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    VerifyEmailSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from .models import PasswordResetToken
from .emails import send_verification_email, send_password_reset_email


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    @swagger_auto_schema(
        operation_summary='Register a new user',
        request_body=RegisterSerializer,
        responses={201: UserSerializer, 400: 'Validation error'},
        tags=['Authentication']
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email(user)
        return Response(
            {'message': 'Account created. Check your email to verify.',
             'user': UserSerializer(user).data},
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    @swagger_auto_schema(
        operation_summary='Login with email and password',
        request_body=LoginSerializer,
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT,
            properties={
                'access': openapi.Schema(type=openapi.TYPE_STRING),
                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
            })},
        tags=['Authentication']
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Logout (blacklist refresh token)',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={'refresh': openapi.Schema(type=openapi.TYPE_STRING)}),
        responses={205: 'Logged out', 400: 'Invalid token'},
        tags=['Authentication']
    )
    def post(self, request):
        try:
            token = RefreshToken(request.data['refresh'])
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except (TokenError, KeyError):
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    # Uses simplejwt's built-in TokenRefreshView logic
    # See urls.py — we wrap it for swagger docs


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='Verify email address',
        request_body=VerifyEmailSerializer,
        responses={200: 'Email verified', 400: 'Invalid/expired token'},
        tags=['Authentication']
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_obj = serializer.token_obj
        token_obj.user.is_email_verified = True
        token_obj.user.save(update_fields=['is_email_verified'])
        token_obj.delete()
        return Response({'message': 'Email verified successfully'})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    @swagger_auto_schema(
        operation_summary='Request password reset email',
        request_body=ForgotPasswordSerializer,
        responses={200: 'Email sent if account exists'},
        tags=['Authentication']
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            from .models import User
            user = User.objects.get(email=email)
            token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            send_password_reset_email(user, token)
        except User.DoesNotExist:
            pass  # Don't reveal whether email exists
        return Response({'message': 'If that email exists, a reset link was sent.'})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='Reset password using token',
        request_body=ResetPasswordSerializer,
        responses={200: 'Password reset', 400: 'Invalid token or password'},
        tags=['Authentication']
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_obj = serializer.reset_obj
        user = reset_obj.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        reset_obj.is_used = True
        reset_obj.save()
        return Response({'message': 'Password reset successfully'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Get current user profile',
        responses={200: UserSerializer},
        tags=['Authentication']
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)