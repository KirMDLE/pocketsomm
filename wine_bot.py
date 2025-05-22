import asyncio
import os
import random
import aiohttp
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
)
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes
)
import nest_asyncio

nest_asyncio.apply()

os.environ['TZ'] = 'Europe/Moscow'
TOKEN = ""  # Insert your bot token here

CATEGORIES = {
    "reds": {
        "url": "https://api.sampleapis.com/wines/reds",
        "description": "Bold, rich and full-bodied red wines. Pairs well with meat dishes. Avg. price: $15–40."
    },
    "whites": {
        "url": "https://api.sampleapis.com/wines/whites",
        "description": "Crisp, fresh and fruity white wines. Great for poultry or fish. Avg. price: $12–35."
    },
    "rose": {
        "url": "https://api.sampleapis.com/wines/rose",
        "description": "Light, refreshing and slightly sweet. Perfect for summer evenings. Avg. price: $10–30."
    },
    "sparkling": {
        "url": "https://api.sampleapis.com/wines/sparkling",
        "description": "Bubbly and festive. Ideal for celebrations. Avg. price: $20–50."
    },
    "port": {
        "url": "https://api.sampleapis.com/wines/port",
        "description": "Sweet, strong, and rich. Often served after meals. Avg. price: $25–60."
    },
    "dessert": {
        "url": "https://api.sampleapis.com/wines/dessert",
        "description": "Very sweet and often fruity. Best with desserts or cheese. Avg. price: $15–40."
    },
}

user_favorites = {}  # user_id: set of wine IDs

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🍷 Find a wine", callback_data="start_questionnaire")],
        [InlineKeyboardButton("📷 Scan a bottle (soon)", callback_data="not_implemented")],
    ]
    await update.message.reply_text(
        "Welcome! I'm your pocket sommelier. I'll help you choose a wine that fits your taste, budget, and purpose.\n\nYou can:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def not_implemented(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("This feature is under development.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "start_questionnaire":
        context.user_data.clear()
        await ask_price_preference(query)

    elif data.startswith("price_"):
        context.user_data["price"] = data
        await ask_purpose(query)

    elif data.startswith("purpose_"):
        context.user_data["purpose"] = data
        await ask_wine_type(query)

    elif data.startswith("type_"):
        context.user_data["type"] = data
        await suggest_wine(query, context)

    elif data == "back_to_price":
        await ask_price_preference(query)

    elif data == "back_to_purpose":
        await ask_purpose(query)

    elif data.startswith("fav_add:"):
        wine_id = int(data.split(":")[1])
        user_favorites.setdefault(user_id, set()).add(wine_id)
        await query.edit_message_reply_markup(reply_markup=wine_keyboard(wine_id, user_id))

    elif data.startswith("fav_remove:"):
        wine_id = int(data.split(":")[1])
        user_favorites.setdefault(user_id, set()).discard(wine_id)
        await query.edit_message_reply_markup(reply_markup=wine_keyboard(wine_id, user_id))

async def ask_price_preference(query):
    keyboard = [
        [InlineKeyboardButton("Price doesn’t matter", callback_data="price_any")],
        [InlineKeyboardButton("I care about value", callback_data="price_mid")],
        [InlineKeyboardButton("Looking for good deals", callback_data="price_smart")],
        [InlineKeyboardButton("Willing to pay for quality", callback_data="price_premium")],
    ]
    await query.edit_message_text(
        "💰 *How much does price matter to you?*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def ask_purpose(query):
    keyboard = [
        [InlineKeyboardButton("🎁 Gift", callback_data="purpose_gift")],
        [InlineKeyboardButton("🧳 Collection", callback_data="purpose_collection")],
        [InlineKeyboardButton("🍽️ Dinner", callback_data="purpose_dinner")],
        [InlineKeyboardButton("🎉 For a party", callback_data="purpose_party")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_price")],
    ]
    await query.edit_message_text(
        "🎯 *What's the purpose of your purchase?*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def ask_wine_type(query):
    keyboard = [
        [InlineKeyboardButton("Red 🍷", callback_data="type_reds")],
        [InlineKeyboardButton("White 🥂", callback_data="type_whites")],
        [InlineKeyboardButton("Rosé 🌸", callback_data="type_rose")],
        [InlineKeyboardButton("Sparkling 🍾", callback_data="type_sparkling")],
        [InlineKeyboardButton("Dessert 🍮", callback_data="type_dessert")],
        [InlineKeyboardButton("Port 🍷🔥", callback_data="type_port")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_purpose")],
    ]

    descriptions = "\n\n".join([
        f"*{name.capitalize()}*: {info['description']}"
        for name, info in CATEGORIES.items()
    ])

    await query.edit_message_text(
        f"🎨 *Choose your wine preference:*\n\n{descriptions}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def wine_keyboard(wine_id: int, user_id: int) -> InlineKeyboardMarkup:
    favs = user_favorites.get(user_id, set())
    if wine_id in favs:
        button = InlineKeyboardButton("❌ Remove from Favorites", callback_data=f"fav_remove:{wine_id}")
    else:
        button = InlineKeyboardButton("💖 Add to Favorites", callback_data=f"fav_add:{wine_id}")
    return InlineKeyboardMarkup([[button]])

async def suggest_wine(query, context: ContextTypes.DEFAULT_TYPE):
    wine_type = context.user_data.get("type", "type_reds").replace("type_", "")
    wine_data = CATEGORIES.get(wine_type)

    if not wine_data:
        await query.edit_message_text("Error: wine category not found.")
        return

    url = wine_data["url"]

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            wines = await resp.json()

    if not wines:
        await query.edit_message_text("Sorry, no wines found for your preferences.")
        return

    wine = random.choice(wines)
    wine_id = wines.index(wine)
    name = wine.get("wine", "Unnamed")
    winery = wine.get("winery", "Unknown")
    rating = wine.get("rating", {}).get("average", "No rating")
    image_url = wine.get("image")

    text = f"🍷 *{name}*\n🏭 Winery: {winery}\n⭐ Rating: {rating}\n\nHope this is what you're looking for!"

    if image_url:
        await query.edit_message_media(
            InputMediaPhoto(media=image_url, caption=text, parse_mode="Markdown")
        )
    else:
        await query.edit_message_text(text, parse_mode="Markdown")

    await query.edit_message_reply_markup(reply_markup=wine_keyboard(wine_id, query.from_user.id))

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    favs = user_favorites.get(user_id, set())
    if not favs:
        await update.message.reply_text("You have no favorite wines yet.")
        return

    message_lines = []
    for wine_type, category in CATEGORIES.items():
        async with aiohttp.ClientSession() as session:
            async with session.get(category["url"]) as resp:
                wines = await resp.json()
        for wine_id in favs:
            if wine_id < len(wines) and wine_type == context.user_data.get("type", "reds"):
                wine = wines[wine_id]
                name = wine.get("wine", "Unnamed")
                message_lines.append(f"🍷 {name} ({wine_type.capitalize()})")

    if not message_lines:
        await update.message.reply_text("No favorite wines found in your current preferences.")
        return

    await update.message.reply_text("\n".join(message_lines))

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("favorites", show_favorites))
    app.add_handler(CallbackQueryHandler(handle_callback))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
