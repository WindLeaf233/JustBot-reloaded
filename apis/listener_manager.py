from JustBot.apis import Listener
from JustBot.events import PrivateMessageEvent, GroupMessageEvent
from JustBot.matchers import KeywordsMatcher, CommandMatcher
from JustBot.utils import Logger

from typing import Type, Union

import asyncio


class ListenerManager:
    def __init__(self) -> None:
        self.l = {}
        self.logger = Logger('Api/ListenerManager')

    def join(self, listener: Listener, priority: int = 1,
             matcher: Union[KeywordsMatcher, CommandMatcher] = None,
             parameters_convert: Type[Union[str, list, dict, None]] = str) -> None:
        lists: list = [] if not str(priority) in self.l.keys() else self.l[str(priority)]
        lists.append({'listener': listener,
                      'matcher': matcher,
                      'parameters_convert': parameters_convert})
        self.l[str(priority)] = lists
        new_l = {}
        for i in sorted(self.l.items(), reverse=True):
            new_l[i[0]] = i[1]
        self.l = new_l

    def execute(self, event_type: Type[Union[PrivateMessageEvent, GroupMessageEvent]],
                message: str, event: Union[PrivateMessageEvent, GroupMessageEvent]) -> None:
        for priority in self.l.keys():
            for listener_obj in self.l[priority]:
                listener = listener_obj['listener']
                if listener.event == event_type:
                    matcher = listener_obj['matcher']

                    def run_target():
                        self.__run_target(listener, event, message,
                                          isinstance(matcher, CommandMatcher),
                                          listener_obj['parameters_convert'])

                    if matcher:
                        if matcher.match(message):
                            run_target()
                    else:
                        run_target()

    def __run_target(self, listener: Listener, event: Union[PrivateMessageEvent, GroupMessageEvent], message: str,
                     is_command_matcher: bool, parameters_convert: Type[Union[str, list, dict, None]]):
        run_mapping = {
            (lambda: asyncio.run(listener.target(event=event))): False,
            (lambda: asyncio.run(listener.target(event=event, message=message))): False,
            (lambda: asyncio.run(
                listener.target(event=event,
                                command=message.split()[0] if is_command_matcher else None,
                                parameters=self.__get_parameters(message, parameters_convert)
                                if is_command_matcher else None))): False
        }
        for target in run_mapping.keys():
            try:
                target()
                break
            except TypeError as e:
                run_mapping[target] = True
                continue

        if list(set(run_mapping.values())) == [True]:
            self.logger.warning(f'无法回调函数 [light_green]{listener.target}[/light_green], 因为它的定义不规范!')

    @staticmethod
    def __get_parameters(message: str, parameters_convert: Type[Union[str, list, dict, None]]) -> dict:
        def __get_multi_parameters() -> list or dict:
            _dict = {}
            _list = []
            for i in message.split()[1:]:
                k = i.split('=')
                if len(k) == 2:
                    _dict[k[0]] = k[1]
                else:
                    _list.append(k[0])
            return [_dict, _list] if _list else _dict

        return {
            str: ' '.join(message.split()[1:]),
            list: message.split()[1:],
            dict: __get_multi_parameters(),
            None: None
        }[parameters_convert]
