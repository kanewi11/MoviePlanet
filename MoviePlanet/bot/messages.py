from .config import CHANNELS_TO_SUBSCRIBE


msg_start = '<b>Привет, {}!</b>' \
            '\n\nОтправь мне название фильма или сериала. 💬\n' \
            'Пожалуйста, <b>без ошибок!</b> 😉\n\n' \
            '<b>Например:</b>\n' \
            '<i>Зеленая миля</i>'


msg_help = '<b>Как пользоваться?</b>\n\n' \
            '<i>Просто отправь мне название фильма или сериала</i>  💭📤\n\n' \
            'Например:\n' \
            '<b>Зеленая миля</b>\n\n' \
            '<b>Бот не находит фильмы?</b>\n\n' \
            '<b>1.</b> <i>Возможно вы допустили ошибку, проверьте свой запрос.</i>\n'\
            '<b>2.</b> <i>Просто подождите, идет техническое обслуживание.\n' \
            'Оно занимает примерно <b>30 минут</b>.</i>'

str_groups = '\n👉🏻 '.join(CHANNELS_TO_SUBSCRIBE)
msg_if_not_subscribed = f'Сначала подпишись на нас, чтобы не потеряться:\n\n👉🏻 ' \
                        f'{str_groups}\n\n' \
                        f'А после ищи, что душе угодно.\n\n' \
                        f'<i>Это сделано для того, чтобы мы могли функционировать, и ты мог смотреть фильмы ' \
                        f'и сериалы бесплатно.\n\n' \
                        f'<b>Cпасибо за понимание!</b></i>' \
                        f'\n\n<i>Подписался? Напиши название фильма или сериала ⬇️</i>'
