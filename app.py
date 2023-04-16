from textwrap import dedent
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Если нужно конвертировать фото таблицы "
                                   "техника в csv, то просто отправьте мне изображние *двух* столбцов. "
                                   "Если нужно расчитать погрешность, то отправьте мне *начальное* значение топлива.",
                                   parse_mode=ParseMode.MARKDOWN)


async def get_fuel_data(text):
    return float("". join(c for c in text.replace(",", ".") if c.isdigit() or c == ".").strip("."))


async def measurement_error(update, context):

    if "fact" in context.user_data:

        num = await get_fuel_data(update.message.text)
        # context.user_data["volume"] = num
        await update.message.reply_text(f"Объем бака: {num} л")

        event_volume = round(abs(context.user_data["init"] - context.user_data["final"]), 2)
        event_dif = round(abs(context.user_data["fact"] - event_volume), 2)
        meas_error = round(event_dif/num*100, 2)

        if context.user_data["event"] == "drain":
            await update.message.reply_text(dedent(f'''
            Начальный объем: {context.user_data["init"]} л
            Конечный объем: {context.user_data["final"]} л
            Объем слива в СМТ: {event_volume} л
            Фактический объем слива: {context.user_data["fact"]} л
            Разница сливов: {event_dif} л
            Погрешность: {meas_error} %
            '''))
        else:
            await update.message.reply_text(dedent(f'''
            Начальный объем: {context.user_data["init"]} л
            Конечный объем: {context.user_data["final"]} л
            Объем заправки в СМТ: {event_volume} л
            Фактический объем заправки: {context.user_data["fact"]} л
            Разница заправок: {event_dif} л
            Погрешность: {meas_error} %
            '''))

        context.user_data.clear()
        await update.message.reply_text("Введите начальное значение...")

    elif "final" in context.user_data:

        num = await get_fuel_data(update.message.text)
        context.user_data["fact"] = num

        if context.user_data["event"] == "drain":
            await update.message.reply_text(f"Фактический объем слива: {num} л")
        else:
            await update.message.reply_text(f"Фактический объем заправки: {num} л")
        await update.message.reply_text("Введите объем бака...")

    elif "init" in context.user_data:

        num = await get_fuel_data(update.message.text)
        context.user_data["final"] = num
        await update.message.reply_text(f"Конечный объем: {num} л")

        if num > context.user_data["init"]:
            event = "refueling"
            await update.message.reply_text("Введите фактический объем заправки...")
        else:
            event = "drain"
            await update.message.reply_text("Введите фактический объем слива...")
        context.user_data["event"] = event

    else:

        num = await get_fuel_data(update.message.text)
        context.user_data["init"] = num

        await update.message.reply_text(f"Начальный объем: {num} л")
        await update.message.reply_text("Введите конечный объем...")


async def reset(update, context):

    context.user_data.clear()
    await update.message.reply_text("Введите начальное значение...")


async def calibration_photo(update, context):

    file = await update.message.effective_attachment[-1].get_file()
    await file.download_to_drive("calibration_photo")
    await context.bot.send_document(chat_id=update.effective_chat.id, document="calibration_photo")


async def error_handler(update, context):

    await update.message.reply_text("Ошибочка(, попробуйте еще раз")
    print(context.error)

if __name__ == '__main__':

    application = Application.builder().token("5646146728:AAHsLsGMw0Ot4lhAWoeoTRk_XXmXPbVOuR4").build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    measurement_error_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), measurement_error)
    application.add_handler(measurement_error_handler)

    calibration_photo_handler = MessageHandler(filters.PHOTO, calibration_photo)
    application.add_handler(calibration_photo_handler)

    reset_handler = CommandHandler("reset", reset)
    application.add_handler(reset_handler)

    application.add_error_handler(error_handler)

    application.run_polling()
