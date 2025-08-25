"""
Galley Connect Recipe Schema
Compatible with Schema.org Recipe structured data for SEO optimization
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, date
from enum import Enum
import json
import uuid

class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    INTERMEDIATE = "intermediate"
    HARD = "hard"
    EXPERT = "expert"

class WeatherSuitability(Enum):
    ANY_WEATHER = "any-weather"
    CALM_SEAS = "calm-seas"
    ROUGH_WEATHER = "rough-weather"
    PROTECTED_WATERS = "protected-waters"

class DietaryRestriction(Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten-free"
    DAIRY_FREE = "dairy-free"
    NUT_FREE = "nut-free"
    KETO = "keto"
    PALEO = "paleo"
    LOW_CARB = "low-carb"
    HALAL = "halal"
    KOSHER = "kosher"

class MealType(Enum):
    BREAKFAST = "breakfast"
    BRUNCH = "brunch"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    APPETIZER = "appetizer"
    DESSERT = "dessert"
    BEVERAGE = "beverage"

class CuisineType(Enum):
    MEDITERRANEAN = "mediterranean"
    ITALIAN = "italian"
    FRENCH = "french"
    ASIAN = "asian"
    AMERICAN = "american"
    MEXICAN = "mexican"
    CARIBBEAN = "caribbean"
    SEAFOOD = "seafood"
    FUSION = "fusion"
    INTERNATIONAL = "international"

@dataclass
class NutritionInformation:
    """Schema.org NutritionInformation compatible"""
    calories: Optional[int] = None
    carbohydrate_content: Optional[str] = None  # e.g., "20g"
    cholesterol_content: Optional[str] = None
    fat_content: Optional[str] = None
    fiber_content: Optional[str] = None
    protein_content: Optional[str] = None
    saturated_fat_content: Optional[str] = None
    serving_size: Optional[str] = None
    sodium_content: Optional[str] = None
    sugar_content: Optional[str] = None
    trans_fat_content: Optional[str] = None
    unsaturated_fat_content: Optional[str] = None

@dataclass
class RecipeIngredient:
    """Enhanced ingredient with yacht-specific considerations"""
    name: str
    amount: Optional[str] = None  # e.g., "2 cups", "1 kg"
    unit: Optional[str] = None
    notes: Optional[str] = None
    substitutions: Optional[List[str]] = None
    storage_requirements: Optional[str] = None  # galley-specific
    procurement_difficulty: Optional[int] = None  # 1-5 scale for remote locations
    
    def to_schema_org_format(self) -> str:
        """Convert to Schema.org Recipe ingredient format"""
        if self.amount:
            return f"{self.amount} {self.name}"
        return self.name

@dataclass
class RecipeInstruction:
    """Schema.org HowToStep compatible instruction"""
    step_number: int
    text: str
    image: Optional[str] = None  # URL to step image
    video: Optional[str] = None  # URL to step video
    equipment: Optional[List[str]] = None
    time_required: Optional[str] = None  # ISO 8601 duration format
    galley_tip: Optional[str] = None  # Yacht-specific advice

@dataclass
class Equipment:
    """Galley equipment requirements"""
    name: str
    essential: bool = True
    alternatives: Optional[List[str]] = None
    galley_notes: Optional[str] = None

@dataclass
class Chef:
    """Recipe author/chef information - Schema.org Person compatible"""
    id: str
    name: str
    email: Optional[str] = None
    yacht_name: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    certifications: Optional[List[str]] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    social_media: Optional[Dict[str, str]] = None  # platform: url

@dataclass
class YachtSpecificData:
    """Yacht galley specific considerations"""
    galley_notes: Optional[str] = None
    weather_suitability: Optional[WeatherSuitability] = None
    sea_state_recommendations: Optional[str] = None
    storage_tips: Optional[str] = None
    equipment_alternatives: Optional[List[str]] = None
    provisioning_notes: Optional[str] = None
    guest_service_tips: Optional[str] = None
    advance_prep_time: Optional[str] = None  # How much can be prepped ahead

@dataclass
class RecipeRating:
    """Schema.org AggregateRating compatible"""
    rating_value: float  # 1-5 scale
    rating_count: int
    best_rating: int = 5
    worst_rating: int = 1

@dataclass
class GalleyConnectRecipe:
    """
    Complete recipe schema compatible with Schema.org Recipe
    Enhanced for yacht chef collaboration
    """
    # Core Schema.org Recipe fields
    id: str
    name: str  # Schema.org: name
    description: str
    author: Chef  # Schema.org: author (Person)
    date_published: datetime  # Schema.org: datePublished
    date_modified: Optional[datetime] = None  # Schema.org: dateModified
    
    # Recipe specifics
    recipe_ingredients: List[RecipeIngredient] = None  # Schema.org: recipeIngredient
    recipe_instructions: List[RecipeInstruction] = None  # Schema.org: recipeInstructions
    recipe_yield: Optional[str] = None  # Schema.org: recipeYield (e.g., "4 servings")
    prep_time: Optional[str] = None  # Schema.org: prepTime (ISO 8601 duration)
    cook_time: Optional[str] = None  # Schema.org: cookTime
    total_time: Optional[str] = None  # Schema.org: totalTime
    
    # Classification
    recipe_category: Optional[List[MealType]] = None  # Schema.org: recipeCategory
    recipe_cuisine: Optional[List[CuisineType]] = None  # Schema.org: recipeCuisine
    keywords: Optional[List[str]] = None  # Schema.org: keywords
    
    # Dietary and difficulty
    suitable_for_diet: Optional[List[DietaryRestriction]] = None  # Schema.org: suitableForDiet
    difficulty_level: Optional[DifficultyLevel] = None
    
    # Media
    image: Optional[List[str]] = None  # Schema.org: image (URLs)
    video: Optional[str] = None  # Schema.org: video
    
    # Nutrition
    nutrition: Optional[NutritionInformation] = None  # Schema.org: nutrition
    
    # Equipment
    equipment: Optional[List[Equipment]] = None
    
    # Ratings and reviews
    aggregate_rating: Optional[RecipeRating] = None  # Schema.org: aggregateRating
    
    # Yacht-specific data
    yacht_data: Optional[YachtSpecificData] = None
    
    # Metadata
    language: str = "en"  # Schema.org: inLanguage
    license: Optional[str] = None  # Creative Commons, etc.
    is_premium: bool = False
    visibility: str = "public"  # public, private, premium
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        """Set default values and validate"""
        if self.recipe_ingredients is None:
            self.recipe_ingredients = []
        if self.recipe_instructions is None:
            self.recipe_instructions = []
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_schema_org_json_ld(self) -> Dict[str, Any]:
        """
        Convert recipe to Schema.org JSON-LD format for SEO
        Perfect for embedding in web pages
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Recipe",
            "@id": f"https://galleyconnect.com/recipe/{self.id}",
            "name": self.name,
            "description": self.description,
            "datePublished": self.date_published.isoformat(),
            "author": {
                "@type": "Person",
                "name": self.author.name,
                "description": f"Yacht Chef aboard {self.author.yacht_name}" if self.author.yacht_name else "Professional Yacht Chef"
            },
            "recipeIngredient": [ing.to_schema_org_format() for ing in self.recipe_ingredients],
            "recipeInstructions": [
                {
                    "@type": "HowToStep",
                    "name": f"Step {inst.step_number}",
                    "text": inst.text,
                    "position": inst.step_number
                } for inst in self.recipe_instructions
            ]
        }
        
        # Add optional fields if present
        if self.date_modified:
            schema["dateModified"] = self.date_modified.isoformat()
        
        if self.recipe_yield:
            schema["recipeYield"] = self.recipe_yield
            
        if self.prep_time:
            schema["prepTime"] = self.prep_time
            
        if self.cook_time:
            schema["cookTime"] = self.cook_time
            
        if self.total_time:
            schema["totalTime"] = self.total_time
            
        if self.recipe_category:
            schema["recipeCategory"] = [cat.value for cat in self.recipe_category]
            
        if self.recipe_cuisine:
            schema["recipeCuisine"] = [cuisine.value for cuisine in self.recipe_cuisine]
            
        if self.keywords:
            schema["keywords"] = ", ".join(self.keywords)
            
        if self.suitable_for_diet:
            schema["suitableForDiet"] = [diet.value for diet in self.suitable_for_diet]
            
        if self.image:
            schema["image"] = self.image
            
        if self.video:
            schema["video"] = {
                "@type": "VideoObject",
                "contentUrl": self.video
            }
            
        if self.nutrition:
            nutrition_schema = {
                "@type": "NutritionInformation"
            }
            if self.nutrition.calories:
                nutrition_schema["calories"] = f"{self.nutrition.calories} calories"
            if self.nutrition.protein_content:
                nutrition_schema["proteinContent"] = self.nutrition.protein_content
            if self.nutrition.fat_content:
                nutrition_schema["fatContent"] = self.nutrition.fat_content
            if self.nutrition.carbohydrate_content:
                nutrition_schema["carbohydrateContent"] = self.nutrition.carbohydrate_content
            
            schema["nutrition"] = nutrition_schema
            
        if self.aggregate_rating:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": self.aggregate_rating.rating_value,
                "ratingCount": self.aggregate_rating.rating_count,
                "bestRating": self.aggregate_rating.best_rating,
                "worstRating": self.aggregate_rating.worst_rating
            }
        
        return schema
    
    def to_json(self, include_yacht_data: bool = True) -> str:
        """Convert to JSON string for storage/export"""
        data = asdict(self)
        if not include_yacht_data:
            data.pop('yacht_data', None)
        return json.dumps(data, default=str, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GalleyConnectRecipe':
        """Create recipe from JSON string"""
        data = json.loads(json_str)
        return cls(**data)
    
    def generate_seo_title(self) -> str:
        """Generate SEO-optimized title"""
        base_title = self.name
        
        # Add cuisine if specified
        if self.recipe_cuisine:
            cuisine = self.recipe_cuisine[0].value.title()
            base_title = f"{cuisine} {base_title}"
        
        # Add yacht-specific appeal
        if self.yacht_data and self.yacht_data.weather_suitability:
            weather = self.yacht_data.weather_suitability.value.replace('-', ' ').title()
            base_title += f" - Perfect for {weather}"
        
        # Add author yacht for credibility
        if self.author.yacht_name:
            base_title += f" | {self.author.yacht_name} Recipe"
        else:
            base_title += " | Yacht Chef Recipe"
            
        return base_title
    
    def generate_seo_description(self) -> str:
        """Generate SEO meta description"""
        description = self.description[:100] + "..." if len(self.description) > 100 else self.description
        
        # Add yacht chef credibility
        chef_credit = f"by yacht chef {self.author.name}"
        if self.author.yacht_name:
            chef_credit += f" from {self.author.yacht_name}"
        
        # Add key details
        details = []
        if self.prep_time:
            details.append(f"Prep: {self.prep_time}")
        if self.cook_time:
            details.append(f"Cook: {self.cook_time}")
        if self.recipe_yield:
            details.append(f"Serves: {self.recipe_yield}")
        
        detail_str = " | ".join(details)
        
        return f"{description} {chef_credit}. {detail_str}"
    
    def generate_seo_keywords(self) -> List[str]:
        """Generate SEO keywords"""
        keywords = []
        
        # Base keywords
        keywords.extend([
            "yacht chef recipe",
            "galley cooking",
            "boat recipe",
            "marine chef",
            self.name.lower()
        ])
        
        # Add cuisine keywords
        if self.recipe_cuisine:
            for cuisine in self.recipe_cuisine:
                keywords.append(f"{cuisine.value} yacht recipe")
                keywords.append(f"boat {cuisine.value}")
        
        # Add dietary keywords
        if self.suitable_for_diet:
            for diet in self.suitable_for_diet:
                keywords.append(f"{diet.value} yacht recipe")
                keywords.append(f"galley {diet.value}")
        
        # Add meal type keywords
        if self.recipe_category:
            for category in self.recipe_category:
                keywords.append(f"yacht {category.value}")
                keywords.append(f"boat {category.value}")
        
        # Add yacht-specific keywords
        if self.yacht_data:
            if self.yacht_data.weather_suitability:
                weather = self.yacht_data.weather_suitability.value
                keywords.append(f"{weather} recipe")
                keywords.append(f"galley {weather}")
        
        # Add existing keywords
        if self.keywords:
            keywords.extend(self.keywords)
        
        return list(set(keywords))  # Remove duplicates

# Helper functions for database integration

def minutes_to_iso8601(minutes: int) -> str:
    """Convert minutes to ISO 8601 duration format"""
    if minutes < 60:
        return f"PT{minutes}M"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"PT{hours}H"
        else:
            return f"PT{hours}H{remaining_minutes}M"

def iso8601_to_minutes(duration: str) -> int:
    """Convert ISO 8601 duration to minutes"""
    # Simple parser for PT##H##M format
    if not duration.startswith('PT'):
        return 0
    
    duration = duration[2:]  # Remove PT
    minutes = 0
    
    if 'H' in duration:
        hours_part = duration.split('H')[0]
        minutes += int(hours_part) * 60
        duration = duration.split('H')[1] if 'H' in duration else ""
    
    if 'M' in duration:
        minutes_part = duration.split('M')[0]
        if minutes_part:
            minutes += int(minutes_part)
    
    return minutes

# Example usage and validation
def create_sample_recipe() -> GalleyConnectRecipe:
    """Create a sample recipe for testing"""
    chef = Chef(
        id="chef-001",
        name="Captain Marco Rossi",
        yacht_name="Serenity",
        location="Monaco",
        experience_years=15,
        bio="Award-winning yacht chef specializing in Mediterranean cuisine"
    )
    
    ingredients = [
        RecipeIngredient(
            name="Fresh Sea Bass",
            amount="2 lbs",
            notes="Can substitute with any white fish",
            substitutions=["Halibut", "Cod", "Snapper"],
            procurement_difficulty=3
        ),
        RecipeIngredient(
            name="Olive Oil",
            amount="1/4 cup",
            storage_requirements="Cool, dark place"
        ),
        RecipeIngredient(
            name="Lemon",
            amount="2 large",
            storage_requirements="Room temperature for 1 week"
        )
    ]
    
    instructions = [
        RecipeInstruction(
            step_number=1,
            text="Preheat galley oven to 400°F. Pat fish dry and season with salt and pepper.",
            galley_tip="Use the convection setting if available for even cooking in rough seas."
        ),
        RecipeInstruction(
            step_number=2,
            text="Heat olive oil in oven-safe pan. Sear fish skin-side down for 3 minutes.",
            galley_tip="Keep pan stable with galley clamps in rough weather."
        ),
        RecipeInstruction(
            step_number=3,
            text="Flip fish, add lemon juice, and transfer to oven for 10-12 minutes.",
            galley_tip="Fish is done when it flakes easily - don't overcook!"
        )
    ]
    
    yacht_data = YachtSpecificData(
        galley_notes="This recipe works well in any size galley. Keep ingredients secure during preparation.",
        weather_suitability=WeatherSuitability.CALM_SEAS,
        sea_state_recommendations="Best prepared in calm conditions due to hot oil use",
        advance_prep_time="Fish can be seasoned 2 hours ahead"
    )
    
    nutrition = NutritionInformation(
        calories=285,
        protein_content="42g",
        fat_content="12g",
        carbohydrate_content="2g"
    )
    
    recipe = GalleyConnectRecipe(
        id="recipe-001",
        name="Mediterranean Seared Sea Bass",
        description="A classic Mediterranean preparation perfect for impressing charter guests. Simple techniques showcase the fresh fish with bright lemon and quality olive oil.",
        author=chef,
        date_published=datetime.now(),
        recipe_ingredients=ingredients,
        recipe_instructions=instructions,
        recipe_yield="4 servings",
        prep_time="PT15M",
        cook_time="PT20M",
        total_time="PT35M",
        recipe_category=[MealType.DINNER],
        recipe_cuisine=[CuisineType.MEDITERRANEAN],
        suitable_for_diet=[DietaryRestriction.GLUTEN_FREE, DietaryRestriction.DAIRY_FREE],
        difficulty_level=DifficultyLevel.MEDIUM,
        keywords=["sea bass", "mediterranean", "elegant", "charter guests"],
        yacht_data=yacht_data,
        nutrition=nutrition,
        is_premium=False,
        tags=["seafood", "elegant", "quick", "healthy"]
    )
    
    return recipe

if __name__ == "__main__":
    # Test the schema
    sample_recipe = create_sample_recipe()
    
    print("=== SEO TITLE ===")
    print(sample_recipe.generate_seo_title())
    
    print("\n=== SEO DESCRIPTION ===")
    print(sample_recipe.generate_seo_description())
    
    print("\n=== SEO KEYWORDS ===")
    print(", ".join(sample_recipe.generate_seo_keywords()))
    
    print("\n=== SCHEMA.ORG JSON-LD ===")
    print(json.dumps(sample_recipe.to_schema_org_json_ld(), indent=2))
    
    print("\n=== FULL JSON EXPORT ===")
    print(sample_recipe.to_json())