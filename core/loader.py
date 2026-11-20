import importlib
import pkgutil

from aiogram import Bot, Dispatcher


async def load_modules(bot: Bot, dp: Dispatcher):
    import modules

    candidates = []
    for info in pkgutil.iter_modules(modules.__path__):
        if info.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"modules.{info.name}")
            setup = getattr(module, "setup", None)
            if not callable(setup):
                print(f"Модуль {info.name} пропущен: нет функции setup")
                continue
            order = getattr(module, "order", 100)
            if isinstance(order, bool):
                raise ValueError("order должен быть числом")
            candidates.append((int(order), info.name, module, setup))
        except Exception as error:
            print(f"Ошибка импорта модуля {info.name}: {error}")

    menu_items = []
    for order, name, module, setup in sorted(candidates, key=lambda item: (item[0], item[1])):
        try:
            await setup(bot, dp)
            print(f"Модуль загружен: {name} (order: {order})")
            for item in getattr(module, "MENU_ITEMS", []):
                menu_items.append({
                    "text": item["text"],
                    "callback_data": item["callback_data"],
                    "order": order
                })
        except Exception as error:
            print(f"Ошибка запуска модуля {name}: {error}")

    menu_items.sort(key=lambda item: item["order"])
    return menu_items
