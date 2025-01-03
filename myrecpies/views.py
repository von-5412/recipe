from django.shortcuts import render
from .models import * 
from django.db.models import Avg
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
# Create your views here.
def home(request):
    queryset = Recipe.objects.all()[:4]
    context = {'recipes': queryset}
    return render(request, "new/index.html", context)


@login_required
def add_recipe(request):
    if request.method == 'POST':
        data = request.POST
        recipe_name = data.get('recipe_name')
        recipe_description = data.get('recipe_description')
        instructions = data.get('instructions')
        cooking_time = data.get('cooking_time')
        recipe_image = request.FILES.get('recipe_image')
        default_serving = data.get('default_serving', 1)

        # Create the Recipe instance
        recipe = Recipe.objects.create(
            user=request.user,
            recipe_image=recipe_image,
            recipe_name=recipe_name,
            recipe_description=recipe_description,
            instructions=instructions,
            cooking_time=cooking_time,
            default_serving=default_serving
        )

        # Handle multiple ingredients
        ingredient_names = data.getlist('ingredient_name[]')
        ingredient_quantities = data.getlist('ingredient_quantity[]')

        for name, quantity in zip(ingredient_names, ingredient_quantities):
            Ingredient.objects.create(
                recipe=recipe,
                name=name,
                quantity=quantity
            )

        return redirect('/addrecipe')  # Adjust the redirect as needed
    return render(request, "addrecipe.html")


def viewrecipe(request):
    recipes = Recipe.objects.all()
    paginator = Paginator(recipes, 20)  # Show 20 recipes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'view.html', {'page_obj': page_obj})


@login_required
def delete_recipe(request, id):
    queryset = Recipe.objects.get(id=id)
    queryset.delete()
    return redirect('/viewrecipe')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Recipe, Ingredient

@login_required
def update_recipe(request, id):
    queryset = Recipe.objects.get(id=id)
    
    if request.method == 'POST':
        data = request.POST
        recipe_name = data.get('recipe_name')
        recipe_description = data.get('recipe_description')
        instructions = data.get('instructions')
        cooking_time = data.get('cooking_time')
        recipe_image = request.FILES.get('recipe_image')

        # Update the recipe details
        queryset.recipe_name = recipe_name
        queryset.recipe_description = recipe_description
        queryset.instructions = instructions
        queryset.cooking_time = cooking_time

        # If a new image is uploaded, update it
        if recipe_image:
            queryset.recipe_image = recipe_image

        # Save the updated recipe details
        queryset.save()

        # Handle the ingredients
        ingredient_names = request.POST.getlist('ingredient_name[]')
        ingredient_quantities = request.POST.getlist('ingredient_quantity[]')

        # Remove old ingredients
        queryset.ingredients.all().delete()

        # Add new ingredients
        for name, quantity in zip(ingredient_names, ingredient_quantities):
            if name and quantity:  # Avoid adding empty ingredients
                Ingredient.objects.create(
                    recipe=queryset,
                    name=name,
                    quantity=quantity
                )
        
        # After saving ingredients, redirect to the recipe detail page
        return redirect('recipe_detail', id=queryset.id)

    context = {'recipe': queryset}
    return render(request, "update_recipe.html", context)



def recipe_detail(request, id):
    # Fetching the recipe based on the ID
    queryset = Recipe.objects.get(id=id)

    # Fetch ingredients using related name
    ingredients = queryset.ingredients.all()  # Use related_name 'ingredients'

    # Splitting instructions into a list
    instructions = queryset.instructions.split('.')

    # Handling POST request for rating and commenting
    if request.method == 'POST':
        if request.user.is_authenticated:
            # Rating Logic
            score = request.POST.get('score')
            existing_rating = Rating.objects.filter(user=request.user, recipe_name=queryset).first()
            if score is not None:
                score = int(score)
                if existing_rating:
                    # Update the existing rating
                    existing_rating.score = score
                    existing_rating.save()
                else:
                    # Create a new rating
                    rating = Rating(user=request.user, recipe_name=queryset, score=score)
                    rating.save()

            # Comment Logic
            content = request.POST.get('content')
            if content:
                comment = Comment(user=request.user, recipe_name=queryset, content=content)
                comment.save()
        else:
            messages.error(request, 'Please Login to Rate or Comment.')
        return redirect("recipe_detail", id=id)

    # Fetching comments for the recipe
    comments = Comment.objects.filter(recipe_name=queryset).order_by('-created_at')

    # Calculating the average rating for the recipe
    average_rating = Rating.objects.filter(recipe_name=queryset).aggregate(Avg('score'))['score__avg']

    # Include image URL if available, otherwise None
    image_url = queryset.recipe_image.url if queryset.recipe_image else None

    # Passing context to template, including the servings range
    context = {
        'recipes': queryset,
        'ingredients': ingredients,
        'instructions': instructions,
        'average_rating': average_rating,
        'comments': comments,
        'image': image_url,
        'created_at': queryset.created_at,
        'created_by': queryset.user,
        'servings_range': range(1, 11),  # Adding the range of 1 to 10 for servings
    }

    return render(request, "recipedetail.html", context)



def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'Invalid username')
            return redirect('/login_page')

        user = authenticate(username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid Password')
            return redirect('/login_page/')
        else:
            login(request, user)
            return redirect('/viewrecipe/')

    return render(request, "login_page.html")


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = User.objects.filter(username=username)
        if user.exists():
            messages.info(request, 'Username already exists')
            return redirect('/register')
        user = User.objects.create(first_name=first_name,
                                   last_name=last_name,
                                   email=email,
                                   username=username)
        user.set_password(password)
        user.save()
        messages.success(request, 'Account Created Successfully')
        return redirect('/register/')

    return render(request, "register.html")


@login_required
def log_out(request):
    logout(request)  # Logs out the user
    return redirect('/login_page')  # Redirects to the desired URL after logout (replace 'home' with the appropriate URL name)


def search(request):
    queryset = Recipe.objects.order_by('-created_at')
    if request.GET.get('search'):
        queryset = queryset.filter(recipe_name__icontains=request.GET.get('search'))
    context = {'recipes': queryset}
    return render(request, "search.html", context)



@login_required
def profile(request, id):
    try:
        # Fetch the user and related profile details
        user = User.objects.get(id=id)
        user_recipes = Recipe.objects.filter(user=user)
        recipe_count = user_recipes.count()
        userdetails = UserProfile.objects.get(user=user)

        # Determine if the profile needs an update (based on your business logic)
        needs_update = False
        if not userdetails.dob or not userdetails.bio:  # Example condition, customize as needed
            needs_update = True

        # Add all the data to the context
        context = {
            'user': user,
            'recipes': user_recipes,
            'userdetails': userdetails,
            'recipe_count': recipe_count,

            'needs_update': needs_update,
        }

        return render(request, "profile.html", context)

    except UserProfile.DoesNotExist:
        return redirect("/create_profile/")
    except User.DoesNotExist:
        return redirect("/")  

def create_profile(request):
    queryset = User.objects.get(username=request.user.username)
    if request.method == 'POST':
        bio = request.POST.get('bio')
        dob = request.POST.get('dob')
        profile_pic = request.FILES.get('profile_pic')
        profile = UserProfile.objects.create(user=queryset,
                                             profile_pic=profile_pic,
                                             bio=bio,
                                             dob=dob)
        messages.success(request, 'Profile Created Successfully')
        profile.save()
        return redirect('profile', id=request.user.id)
    return render(request, "create_prrofile.html")


def update_profile(request, id):
    queryset = UserProfile.objects.get(id=id)
    if request.method == 'POST':
        data = request.POST
        bio = data.get('bio')
        dob = data.get('dob')
        profile_pic = request.FILES.get('profile_pic')
        queryset.dob = dob
        queryset.bio = bio
        if profile_pic:
            queryset.profile_pic = profile_pic
        queryset.save()
        print("User Id", request.user.id)
        return redirect('profile', id=request.user.id)
    context = {'userprofile': queryset}
    return render(request, "updateprofile.html", context)
