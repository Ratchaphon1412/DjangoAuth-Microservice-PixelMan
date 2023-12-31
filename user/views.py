from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import *
# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated

from infrastructure.kafka.producer import ProducerKafka


class RegisterAPIView(APIView):
    def post(self, request):
        """
        Create new user

        Return: Message
        Required: Username, Email, Password, Confirm Password


        """

        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            producer = ProducerKafka()

            # serialized_data = {'user': serializer.data}
            producer.publish('user_create', 'create', serializer.data)
            return Response({"message": "Create User Success!"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(TokenObtainPairView):
    serializer_class = LoginSerializer


class UserProfilesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Authorization 

        Return: User Profile
        Required: Authenticated
        """

        user = request.user
        serializer = UserProfilesSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Update user profile

        Return: Message
        Required: Authenticated

        """

        user = request.user
        serializer = UserProfilesUpdateSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            address = Address.objects.filter(
                address_id=serializer.validated_data.get("address_id")).first()
            if address:
                serializer.update(user, serializer.validated_data)

                return Response({"message": "Update User Success!"}, status=status.HTTP_200_OK)

        return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)


class AddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all address of user

        Return: List of address 
        Required: Authenticated

        """
        user = request.user
        address = Address.objects.filter(user=user)
        serializer = AddressSerializer(address, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create new address

        Return: Message
        Required: Authenticated

        """

        user = request.user
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=user)
            return Response({"message": "Create Address Success!"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        Update address

        Return: Message
        Required: Authenticated

        """
        if not request.data.get("address_id"):
            return Response({"error": "address_id not found in request data"}, status=status.HTTP_400_BAD_REQUEST)

        address = request.user.address_set.filter(
            address_id=request.data.get("address_id")).first()

        serializer = AddressSerializer(address, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.update(address, serializer.validated_data)
            return Response({"message": "Update Address Success!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Delete address

        Return: Message
        Required: Authenticated

        """
        user = request.user

        address_id = request.data.get("address_id")

        if not address_id:
            return Response({"error": "address_id not found in request data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = Address.objects.get(address_id=address_id, user=user)
        except Address.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        address.delete()

        return Response({"message": "Delete Address Success!"}, status=status.HTTP_200_OK)
