class SlackFormatter:
    """
    used to format payloads and messages to send to slack
    """

    @staticmethod
    def add_next_category_button(text: str) -> dict:
        """
        adds next category button to message
        :param text: text to put above button
        :return: json of button message to send to slack
        """
        button_json = {
            "text": text,
            "attachments": [
                {
                    "fallback": "Out of questions in this category!",
                    "callback_id": "cont_cat",
                    "color": "#060CE9",
                    "attachment_type": "default",
                    "actions": [
                            {
                                "name": "continue_category",
                                "text": "Continue Category",
                                "type": "button",
                                "value": "continue_category"
                            }
                        ]
                    }
                ]
            }
        return button_json