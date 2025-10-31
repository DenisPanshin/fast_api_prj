import os

from fastapi import UploadFile
from fastapi.requests import Request
from sqlalchemy.orm import Session

from apps.postapp.models import Post
from core.config import MEDIA_URL, IMG_EXTENSION_LIST


class PostForm:
    def __init__(self, request, context):
        self.context = context
        self.request: Request = request
        self.image = None
        self.title = None
        self.content = None
        self.owner = None
        self.errors = []

    async def load_data(self):
        form = await self.request.form()
        self.image = form.get('image')
        self.title = form.get('title')
        self.content = form.get('content')
        self.owner = self.context.get('user')

        if all([self.image, self.title, self.content]):
            return True
        return False

    async def load_photo_from_form(self):
        await self.load_data()
        image: UploadFile = self.image
        content = await image.read()

        file_name = image.filename.replace(' ', '')
        extension = file_name.split('.')[-1].lower()

        if extension not in IMG_EXTENSION_LIST:
            self.errors.append('Вставьте пожалуйста фотографию')
            return False

        user_name = self.context.get("user").username
        full_path_to_media = os.path.join(MEDIA_URL, user_name)
        if not os.path.exists(full_path_to_media):
            os.makedirs(full_path_to_media)

        with open(os.path.join(full_path_to_media, file_name), 'wb') as f:
            f.write(content)

        return os.path.join(user_name, file_name)


class AddPostForm(PostForm):
    async def create_post(self, db: Session):
        image_path = await self.load_photo_from_form()
        if image_path:
            post = Post(title=self.title, image=image_path,
                         content=self.content, owner=self.owner)
            db.add(post)
            db.commit()
            db.refresh(post)
            return True

        self.errors.append('Возникла неизвестная ошибка')

        return False


class UpdatePostForm(PostForm):

    async def load_photo_from_form(self):

        if self.image.filename:
            return await super().load_photo_from_form()

    async def load_data(self):
        form = await self.request.form()
        self.image: UploadFile = form.get('image')
        self.title = form.get('title')
        self.content = form.get('content')
        self.owner = self.context.get('user')

    async def update_post(self, db: Session, post: Post):
        await self.load_data()
        image_path = await self.load_photo_from_form()
        if self.image and image_path:
            post.image = image_path

        if self.title:
            post.title = self.title

        if self.content:
            post.content = self.content
            print(self.content)

        db.commit()

        return True

