"""Translation module for KouranBot - English and French support."""

TRANSLATIONS = {
    "en": {
        # Commands
        "welcome": "Welcome to KouranBot, {name}!\n\nI'll help you stay informed about scheduled power outages in Mauritius.\n\nAvailable commands:\n/subscribe - Select localities to monitor\n/mysubscriptions - View your subscriptions\n/unsubscribe - Remove all subscriptions\n/language - Change language\n/help - Show this help message\n\nGet started by using /subscribe to choose the localities you want to monitor!",
        "help": "KouranBot - Power Outage Notification Bot\n\nCommands:\n/start - Welcome message\n/subscribe - Select localities to monitor for power outages\n/mysubscriptions - View your current subscriptions\n/unsubscribe - Remove all your subscriptions\n/language - Change language (English/French)\n/help - Show this help message\n\nHow it works:\n1. Subscribe to one or more localities\n2. I'll monitor power outages for those areas\n3. You'll receive notifications when outages are scheduled\n\nStay prepared!",

        # Subscribe flow
        "select_district": "Please select a district:",
        "select_locality": "{district}\nPage {page}/{total}\nSelected: {count} localities\n\nTap a locality to toggle selection:",
        "no_districts": "No districts available. Please contact the administrator.",
        "no_localities": "No localities found for {district}.",
        "subscriptions_saved": "Successfully subscribed to {count} locality/localities!\n\nYou'll receive notifications when power outages are scheduled in these areas.\n\nUse /mysubscriptions to view your subscriptions.",
        "already_subscribed": "You were already subscribed to all selected localities.",
        "no_localities_selected": "No localities selected.",

        # My subscriptions
        "my_subscriptions_header": "Your active subscriptions:\n\n",
        "my_subscriptions_footer": "\nTotal: {count} localities\n\nUse /unsubscribe to remove all subscriptions",
        "no_subscriptions": "You don't have any active subscriptions.\n\nUse /subscribe to start monitoring localities!",

        # Unsubscribe
        "confirm_unsubscribe": "Are you sure you want to remove ALL your subscriptions?",
        "unsubscribed": "Successfully removed {count} subscription(s).",
        "no_subscriptions_to_remove": "You had no active subscriptions.",

        # Language
        "select_language": "Please select your language / Veuillez sélectionner votre langue:",
        "language_changed": "Language changed to English.",

        # Buttons
        "button_previous": "« Previous",
        "button_next": "Next »",
        "button_back": "⬅️ Back",
        "button_confirm": "✅ Confirm",
        "button_cancel": "❌ Cancel",
        "button_yes_unsubscribe": "Yes, unsubscribe all",
        "button_english": "🇬🇧 English",
        "button_french": "🇫🇷 Français",

        # Notifications
        "outage_alert": "⚠️ Power Outage Alert\n\n📍 Locality: {locality}\n🏘️ District: {district}\n📅 Date: {date}\n🕐 From: {from_time}\n🕐 To: {to_time}\n📌 Streets: {streets}\n\nStay prepared!",
        "outage_alert_no_streets": "⚠️ Power Outage Alert\n\n📍 Locality: {locality}\n🏘️ District: {district}\n📅 Date: {date}\n🕐 From: {from_time}\n🕐 To: {to_time}\n\nStay prepared!",

        # General
        "operation_cancelled": "Operation cancelled.",
    },

    "fr": {
        # Commands
        "welcome": "Bienvenue sur KouranBot, {name}!\n\nJe vous aiderai à rester informé des coupures d'électricité programmées à Maurice.\n\nCommandes disponibles:\n/subscribe - Sélectionner les localités à surveiller\n/mysubscriptions - Voir vos abonnements\n/unsubscribe - Supprimer tous les abonnements\n/language - Changer de langue\n/help - Afficher ce message d'aide\n\nCommencez par utiliser /subscribe pour choisir les localités que vous souhaitez surveiller!",
        "help": "KouranBot - Bot de Notification de Coupures d'Électricité\n\nCommandes:\n/start - Message de bienvenue\n/subscribe - Sélectionner les localités à surveiller\n/mysubscriptions - Voir vos abonnements actuels\n/unsubscribe - Supprimer tous vos abonnements\n/language - Changer de langue (Anglais/Français)\n/help - Afficher ce message d'aide\n\nComment ça marche:\n1. Abonnez-vous à une ou plusieurs localités\n2. Je surveillerai les coupures pour ces zones\n3. Vous recevrez des notifications lors de coupures programmées\n\nRestez préparé!",

        # Subscribe flow
        "select_district": "Veuillez sélectionner un district:",
        "select_locality": "{district}\nPage {page}/{total}\nSélectionnées: {count} localités\n\nAppuyez sur une localité pour basculer la sélection:",
        "no_districts": "Aucun district disponible. Veuillez contacter l'administrateur.",
        "no_localities": "Aucune localité trouvée pour {district}.",
        "subscriptions_saved": "Abonnement réussi à {count} localité(s)!\n\nVous recevrez des notifications lorsque des coupures sont programmées dans ces zones.\n\nUtilisez /mysubscriptions pour voir vos abonnements.",
        "already_subscribed": "Vous étiez déjà abonné à toutes les localités sélectionnées.",
        "no_localities_selected": "Aucune localité sélectionnée.",

        # My subscriptions
        "my_subscriptions_header": "Vos abonnements actifs:\n\n",
        "my_subscriptions_footer": "\nTotal: {count} localités\n\nUtilisez /unsubscribe pour supprimer tous les abonnements",
        "no_subscriptions": "Vous n'avez aucun abonnement actif.\n\nUtilisez /subscribe pour commencer à surveiller des localités!",

        # Unsubscribe
        "confirm_unsubscribe": "Êtes-vous sûr de vouloir supprimer TOUS vos abonnements?",
        "unsubscribed": "Suppression réussie de {count} abonnement(s).",
        "no_subscriptions_to_remove": "Vous n'aviez aucun abonnement actif.",

        # Language
        "select_language": "Please select your language / Veuillez sélectionner votre langue:",
        "language_changed": "Langue changée en Français.",

        # Buttons
        "button_previous": "« Précédent",
        "button_next": "Suivant »",
        "button_back": "⬅️ Retour",
        "button_confirm": "✅ Confirmer",
        "button_cancel": "❌ Annuler",
        "button_yes_unsubscribe": "Oui, tout désabonner",
        "button_english": "🇬🇧 English",
        "button_french": "🇫🇷 Français",

        # Notifications
        "outage_alert": "⚠️ Alerte de Coupure d'Électricité\n\n📍 Localité: {locality}\n🏘️ District: {district}\n📅 Date: {date}\n🕐 De: {from_time}\n🕐 À: {to_time}\n📌 Rues: {streets}\n\nRestez préparé!",
        "outage_alert_no_streets": "⚠️ Alerte de Coupure d'Électricité\n\n📍 Localité: {locality}\n🏘️ District: {district}\n📅 Date: {date}\n🕐 De: {from_time}\n🕐 À: {to_time}\n\nRestez préparé!",

        # General
        "operation_cancelled": "Opération annulée.",
    }
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """
    Get translated text for a given language and key.

    Args:
        lang: Language code ('en' or 'fr')
        key: Translation key
        **kwargs: Format arguments for the text

    Returns:
        Translated and formatted text
    """
    # Default to English if language not supported
    if lang not in TRANSLATIONS:
        lang = "en"

    # Get the text, default to English if key not found in selected language
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, f"[Missing: {key}]"))

    # Format the text with provided arguments
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text

    return text


def get_user_language(user_lang: str = None) -> str:
    """
    Validate and return user language code.

    Args:
        user_lang: User's language preference

    Returns:
        Valid language code ('en' or 'fr')
    """
    if user_lang in ["en", "fr"]:
        return user_lang
    return "en"  # Default to English
