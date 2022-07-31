from django.http import Http404
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import filters, pagination, permissions, status, viewsets
from rest_framework.response import Response

from posts.models import Post, Group, Comment, Follow, User
from .permissions import IsAuthor
from .serializers import (PostSerializer,
                          GroupSerializer,
                          CommentSerializer,
                          FollowSerializer,
                          )


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = ((permissions.IsAuthenticatedOrReadOnly & IsAuthor),)
    pagination_class = pagination.LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = ((permissions.IsAuthenticatedOrReadOnly & IsAuthor),)

    def get_queryset(self):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        return Comment.objects.filter(post=post)

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        serializer.save(author=self.request.user, post=post)


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, )
    search_fields = ('following__username', )

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def create(self, data):
        try:
            following = get_object_or_404(
                User,
                username=data.data.get('following')
            )
        except Http404:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if self.request.user == following:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = FollowSerializer(data=data.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer.save(user=self.request.user, following=following)
        except IntegrityError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
