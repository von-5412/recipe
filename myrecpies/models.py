from django.db import models
from django.contrib.auth.models import User
import datetime

# Recipe model
class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe_name = models.CharField(max_length=100)
    recipe_description = models.TextField()
    instructions = models.TextField(default=None)
    cooking_time = models.TextField(default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    recipe_image = models.ImageField(upload_to="recepie")
    default_serving = models.PositiveIntegerField(default=1)

    def average_rating(self):
        total_ratings = Rating.objects.filter(recipe_name=self).count()
        if total_ratings > 0:
            total_score = Rating.objects.filter(recipe_name=self).aggregate(models.Sum('score'))['score__sum']
            average_score = total_score / total_ratings
            return round(average_score, 2)
        return 0

    def __str__(self):
        return self.recipe_name


# Ingredient model (linked to Recipe)
class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50)  # For example, "500 ml", "2 tbsp", etc.

    def __str__(self):
        return f"{self.name} ({self.quantity})"


# Rating model
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe_name = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=None)


# Comment model
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe_name = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# User profile model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True)
    bio = models.TextField(blank=True)
    dob = models.DateField(null=True, blank=True)
    needs_update = models.BooleanField(default=True)

    @property
    def following_count(self):
        return self.followers.count()

    def followers_count(self):
        return self.user.following.count()
