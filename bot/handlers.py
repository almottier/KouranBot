"""Telegram bot command handlers for KouranBot."""

import logging
from typing import Dict, Set

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import LOCALITIES_PER_PAGE, DISTRICTS_PER_ROW
from bot.database import (
    get_db, get_or_create_user, get_all_districts, get_localities_by_district,
    get_user_subscriptions, add_subscription, remove_subscription,
    remove_all_subscriptions, is_subscribed, get_user_language, set_user_language
)
from bot.translations import get_text

logger = logging.getLogger(__name__)

# Store temporary subscription state per user
user_subscription_state: Dict[int, Set[int]] = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    db = get_db()
    try:
        get_or_create_user(db, user.id, user.username, user.language_code)
        lang = get_user_language(db, user.id)
    finally:
        db.close()

    welcome_message = get_text(lang, "welcome", name=user.first_name)
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    user_id = update.effective_user.id
    db = get_db()
    try:
        lang = get_user_language(db, user_id)
    finally:
        db.close()

    help_text = get_text(lang, "help")
    await update.message.reply_text(help_text)


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command - show district selection."""
    user_id = update.effective_user.id

    # Initialize empty subscription state for this user
    user_subscription_state[user_id] = set()

    db = get_db()
    try:
        districts = get_all_districts(db)
        lang = get_user_language(db, user_id)
    finally:
        db.close()

    if not districts:
        await update.message.reply_text(get_text(lang, "no_districts"))
        return

    keyboard = []
    row = []

    for district in districts:
        # Capitalize district name for display
        display_name = district.name.replace("_", " ").title()
        button = InlineKeyboardButton(
            display_name,
            callback_data=f"district_{district.id}"
        )
        row.append(button)

        if len(row) == DISTRICTS_PER_ROW:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Add cancel button
    keyboard.append([InlineKeyboardButton(
        get_text(lang, "button_cancel"),
        callback_data="cancel"
    )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        get_text(lang, "select_district"),
        reply_markup=reply_markup
    )


async def mysubscriptions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mysubscriptions command."""
    user_id = update.effective_user.id

    db = get_db()
    try:
        subscriptions = get_user_subscriptions(db, user_id)
        lang = get_user_language(db, user_id)
    finally:
        db.close()

    if not subscriptions:
        await update.message.reply_text(get_text(lang, "no_subscriptions"))
        return

    # Group by district
    by_district = {}
    for locality in subscriptions:
        district_name = locality.district.name.replace("_", " ").title()
        if district_name not in by_district:
            by_district[district_name] = []
        by_district[district_name].append(locality.name)

    message = get_text(lang, "my_subscriptions_header")
    for district, localities in sorted(by_district.items()):
        message += f"{district}:\n"
        for locality in sorted(localities):
            message += f"  • {locality}\n"
        message += "\n"

    message += get_text(lang, "my_subscriptions_footer", count=len(subscriptions))

    await update.message.reply_text(message)


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unsubscribe command - confirm before removing all subscriptions."""
    user_id = update.effective_user.id
    db = get_db()
    try:
        lang = get_user_language(db, user_id)
    finally:
        db.close()

    keyboard = [
        [
            InlineKeyboardButton(
                get_text(lang, "button_yes_unsubscribe"),
                callback_data="confirm_unsubscribe"
            ),
            InlineKeyboardButton(
                get_text(lang, "button_cancel"),
                callback_data="cancel"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        get_text(lang, "confirm_unsubscribe"),
        reply_markup=reply_markup
    )


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command - show language selection."""
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        get_text("en", "select_language"),  # Always show in both languages
        reply_markup=reply_markup
    )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages - show menu."""
    user_id = update.effective_user.id
    db = get_db()
    try:
        lang = get_user_language(db, user_id)
    finally:
        db.close()

    # Create a menu with quick action buttons
    keyboard = [
        [InlineKeyboardButton(
            "📍 " + ("Subscribe" if lang == "en" else "S'abonner"),
            callback_data="menu_subscribe"
        )],
        [InlineKeyboardButton(
            "📋 " + ("My Subscriptions" if lang == "en" else "Mes Abonnements"),
            callback_data="menu_mysubscriptions"
        )],
        [InlineKeyboardButton(
            "🌐 " + ("Change Language" if lang == "en" else "Changer de Langue"),
            callback_data="menu_language"
        )],
        [InlineKeyboardButton(
            "❓ " + ("Help" if lang == "en" else "Aide"),
            callback_data="menu_help"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if lang == "en":
        message = "Please select an option below or use one of these commands:\n\n/subscribe - Monitor localities\n/mysubscriptions - View subscriptions\n/language - Change language\n/help - Get help"
    else:
        message = "Veuillez sélectionner une option ci-dessous ou utiliser l'une de ces commandes:\n\n/subscribe - Surveiller des localités\n/mysubscriptions - Voir les abonnements\n/language - Changer de langue\n/help - Obtenir de l'aide"

    await update.message.reply_text(message, reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    callback_data = query.data

    # Get user language
    db = get_db()
    try:
        lang = get_user_language(db, user_id)
    finally:
        db.close()

    # Handle menu button clicks
    if callback_data == "menu_subscribe":
        await query.answer()
        # Delete menu and show district selection
        user_subscription_state[user_id] = set()

        db = get_db()
        try:
            districts = get_all_districts(db)
        finally:
            db.close()

        if not districts:
            await query.edit_message_text(get_text(lang, "no_districts"))
            return

        keyboard = []
        row = []

        for district in districts:
            display_name = district.name.replace("_", " ").title()
            button = InlineKeyboardButton(
                display_name,
                callback_data=f"district_{district.id}"
            )
            row.append(button)

            if len(row) == DISTRICTS_PER_ROW:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton(
            get_text(lang, "button_cancel"),
            callback_data="cancel"
        )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            get_text(lang, "select_district"),
            reply_markup=reply_markup
        )
        return

    if callback_data == "menu_mysubscriptions":
        await query.answer()

        db = get_db()
        try:
            subscriptions = get_user_subscriptions(db, user_id)
        finally:
            db.close()

        if not subscriptions:
            await query.edit_message_text(get_text(lang, "no_subscriptions"))
            return

        # Group by district
        by_district = {}
        for locality in subscriptions:
            district_name = locality.district.name.replace("_", " ").title()
            if district_name not in by_district:
                by_district[district_name] = []
            by_district[district_name].append(locality.name)

        message = get_text(lang, "my_subscriptions_header")
        for district, localities in sorted(by_district.items()):
            message += f"{district}:\n"
            for locality in sorted(localities):
                message += f"  • {locality}\n"
            message += "\n"

        message += get_text(lang, "my_subscriptions_footer", count=len(subscriptions))
        await query.edit_message_text(message)
        return

    if callback_data == "menu_language":
        await query.answer()

        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            get_text("en", "select_language"),
            reply_markup=reply_markup
        )
        return

    if callback_data == "menu_help":
        await query.answer()
        await query.edit_message_text(get_text(lang, "help"))
        return

    # Handle language change
    if callback_data.startswith("lang_"):
        new_lang = callback_data.split("_")[1]
        db = get_db()
        try:
            set_user_language(db, user_id, new_lang)
        finally:
            db.close()

        await query.edit_message_text(get_text(new_lang, "language_changed"))
        return

    if callback_data == "cancel":
        # Clean up state
        if user_id in user_subscription_state:
            del user_subscription_state[user_id]

        await query.edit_message_text(get_text(lang, "operation_cancelled"))
        return

    if callback_data == "confirm_unsubscribe":
        db = get_db()
        try:
            count = remove_all_subscriptions(db, user_id)
        finally:
            db.close()

        if count > 0:
            await query.edit_message_text(
                get_text(lang, "unsubscribed", count=count)
            )
        else:
            await query.edit_message_text(get_text(lang, "no_subscriptions_to_remove"))
        return

    if callback_data.startswith("district_"):
        # District selected - show localities
        district_id = int(callback_data.split("_")[1])
        await show_localities(query, user_id, district_id, page=0)
        return

    if callback_data.startswith("locality_"):
        # Locality toggled
        parts = callback_data.split("_")
        district_id = int(parts[1])
        locality_id = int(parts[2])
        page = int(parts[3])

        # Toggle locality in state
        if user_id not in user_subscription_state:
            user_subscription_state[user_id] = set()

        if locality_id in user_subscription_state[user_id]:
            user_subscription_state[user_id].remove(locality_id)
        else:
            user_subscription_state[user_id].add(locality_id)

        # Refresh the localities view
        await show_localities(query, user_id, district_id, page)
        return

    if callback_data.startswith("page_"):
        # Page navigation
        parts = callback_data.split("_")
        district_id = int(parts[1])
        page = int(parts[2])

        await show_localities(query, user_id, district_id, page)
        return

    if callback_data == "back_to_districts":
        # Go back to district selection
        db = get_db()
        try:
            districts = get_all_districts(db)
            lang = get_user_language(db, user_id)
        finally:
            db.close()

        keyboard = []
        row = []

        for district in districts:
            display_name = district.name.replace("_", " ").title()
            button = InlineKeyboardButton(
                display_name,
                callback_data=f"district_{district.id}"
            )
            row.append(button)

            if len(row) == DISTRICTS_PER_ROW:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton(
            get_text(lang, "button_cancel"),
            callback_data="cancel"
        )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            get_text(lang, "select_district"),
            reply_markup=reply_markup
        )
        return

    if callback_data == "confirm_subscriptions":
        # Save subscriptions to database
        if user_id not in user_subscription_state or not user_subscription_state[user_id]:
            await query.edit_message_text(get_text(lang, "no_localities_selected"))
            return

        db = get_db()
        try:
            # Get or create user
            user = update.effective_user
            get_or_create_user(db, user_id, user.username, user.language_code)

            # Add all selected subscriptions
            added_count = 0
            for locality_id in user_subscription_state[user_id]:
                if add_subscription(db, user_id, locality_id):
                    added_count += 1

        finally:
            db.close()

        # Clean up state
        del user_subscription_state[user_id]

        if added_count > 0:
            await query.edit_message_text(
                get_text(lang, "subscriptions_saved", count=added_count)
            )
        else:
            await query.edit_message_text(get_text(lang, "already_subscribed"))
        return


async def show_localities(query, user_id: int, district_id: int, page: int):
    """Show paginated localities for a district."""
    db = get_db()
    try:
        localities = get_localities_by_district(db, district_id)
        district = db.query(get_all_districts(db)[0].__class__).filter_by(id=district_id).first()
        district_name = district.name.replace("_", " ").title() if district else "Unknown"
        lang = get_user_language(db, user_id)

        # Get currently subscribed localities for this user
        existing_subscriptions = get_user_subscriptions(db, user_id)
        existing_locality_ids = {loc.id for loc in existing_subscriptions}
    finally:
        db.close()

    if not localities:
        await query.edit_message_text(
            get_text(lang, "no_localities", district=district_name)
        )
        return

    # Calculate pagination
    total_pages = (len(localities) - 1) // LOCALITIES_PER_PAGE + 1
    page = max(0, min(page, total_pages - 1))

    start_idx = page * LOCALITIES_PER_PAGE
    end_idx = start_idx + LOCALITIES_PER_PAGE
    page_localities = localities[start_idx:end_idx]

    # Initialize state if needed
    if user_id not in user_subscription_state:
        user_subscription_state[user_id] = set()

    # Build keyboard
    keyboard = []
    for locality in page_localities:
        # Check if this locality is selected (in temp state or already subscribed)
        is_selected = (
            locality.id in user_subscription_state[user_id] or
            locality.id in existing_locality_ids
        )
        prefix = "✓ " if is_selected else "○ "

        button = InlineKeyboardButton(
            f"{prefix}{locality.name}",
            callback_data=f"locality_{district_id}_{locality.id}_{page}"
        )
        keyboard.append([button])

    # Add navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                get_text(lang, "button_previous"),
                callback_data=f"page_{district_id}_{page - 1}"
            )
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                get_text(lang, "button_next"),
                callback_data=f"page_{district_id}_{page + 1}"
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Add footer buttons
    footer = [
        InlineKeyboardButton(get_text(lang, "button_back"), callback_data="back_to_districts"),
        InlineKeyboardButton(get_text(lang, "button_confirm"), callback_data="confirm_subscriptions"),
        InlineKeyboardButton(get_text(lang, "button_cancel"), callback_data="cancel")
    ]
    keyboard.append(footer)

    reply_markup = InlineKeyboardMarkup(keyboard)

    selected_count = len(user_subscription_state[user_id])
    message = get_text(
        lang, "select_locality",
        district=district_name,
        page=page + 1,
        total=total_pages,
        count=selected_count
    )

    await query.edit_message_text(message, reply_markup=reply_markup)
