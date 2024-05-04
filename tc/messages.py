from constants import TCEngine
from message_handler import generate_chatgpt_answer


def create_group_message(account, sender_user_id, input_text):
    if account.keywords:
        keywords = [
            word.strip().lower()
            for word in account.keywords.split(",")
            if word.strip()
        ]
        if not any(keyword in input_text.lower() for keyword in keywords):
            return

        prompt = account.group_message_prompt
        if prompt:
            answer = generate_chatgpt_answer(
                user_id=sender_user_id,
                message=input_text,
                engine=TCEngine.GROUP_MESSAGE,
                system_prompt=prompt,
            )

            return answer


def create_private_message(account, sender_user_id, input_text):
    prompt = account.private_message_prompt
    if prompt:
        answer = generate_chatgpt_answer(
            user_id=sender_user_id,
            message=input_text,
            engine=TCEngine.PRIVATE_MESSAGE,
            system_prompt=prompt,
        )
        return answer
