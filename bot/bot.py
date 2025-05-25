import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from elasticsearch import Elasticsearch
from config.config import TELEGRAM_BOT_TOKEN, ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_INDEX

logging.basicConfig(level=logging.INFO)

# States for conversation
GROCERIES, MEAL_TYPE, PREP_TIME, DIET = range(4)

def start(update: Update, context: CallbackContext):
    """Start command handler: prompts user for groceries."""
    update.message.reply_text('Welcome! Please list the groceries you have (comma separated):')
    return GROCERIES

def groceries(update: Update, context: CallbackContext):
    """Handle groceries input and prompt for meal type."""
    context.user_data['groceries'] = update.message.text.split(',')
    reply_keyboard = [['breakfast', 'lunch', 'dinner', 'snack']]
    update.message.reply_text('What meal type?', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MEAL_TYPE

def meal_type(update: Update, context: CallbackContext):
    """Handle meal type input and prompt for prep time."""
    context.user_data['meal_type'] = update.message.text
    update.message.reply_text('Max preparation time (minutes)?')
    return PREP_TIME

def prep_time(update: Update, context: CallbackContext):
    """Handle prep time input and prompt for diet."""
    context.user_data['prep_time'] = update.message.text
    update.message.reply_text("Any special diet? (e.g. low carb, no sugar, etc. Type 'none' if no special diet)")
    return DIET

def diet(update: Update, context: CallbackContext):
    """Handle diet input, query Elasticsearch, and return a recipe suggestion."""
    context.user_data['diet'] = update.message.text
    es = Elasticsearch([{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT}])
    # Build a query using only 'should' clauses for meal type and ingredients
    query = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"title": context.user_data['meal_type']}}
                ] + [
                    {"match": {"ingredients": g.strip()}} for g in context.user_data['groceries']
                ]
            }
        }
    }
    try:
        res = es.search(index=ELASTICSEARCH_INDEX, body=query)
        if res['hits']['hits']:
            recipe = res['hits']['hits'][0]['_source']
            update.message.reply_text(f"Best match: {recipe['title']}\nIngredients: {recipe['ingredients']}\nInstructions: {recipe['instructions']}")
        else:
            update.message.reply_text('Sorry, no recipes found for your criteria. Try different groceries or meal type.')
    except Exception as e:
        update.message.reply_text(f"Error querying recipes: {e}")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    """Cancel command handler: ends the conversation."""
    update.message.reply_text('Bye!')
    return ConversationHandler.END

def main():
    """Start the Telegram bot and set up the conversation handler."""
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GROCERIES: [MessageHandler(Filters.text & ~Filters.command, groceries)],
            MEAL_TYPE: [MessageHandler(Filters.text & ~Filters.command, meal_type)],
            PREP_TIME: [MessageHandler(Filters.text & ~Filters.command, prep_time)],
            DIET: [MessageHandler(Filters.text & ~Filters.command, diet)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main() 