from playwright.sync_api import sync_playwright
import time
import requests

def parse_thread(thread):
      link = thread.query_selector('a[role="link"]')
      if not link:
            return None

      href = link.get_attribute('href') or ''
      thread_id = href.strip('/').split('/')[-1] if href else None

      strings = thread.inner_text().strip()

      lines = [l for l in strings.split('\n') if l.strip() and l.strip() != '\xa0']

      aria_name = link.get_attribute('aria-label') or ''
      is_group = True if aria_name.startswith("Group chat:") else False
      name = aria_name.replace('Group chat: ', '').strip()
      message = lines[2] if lines[1] == "Unread message:" else lines[1]

      if is_group:
            thread_name = aria_name.replace('Group chat:', '').strip()
            if ':' in message:
                  message = message.split(":", 1)
                  content = message[1]
                  sender = message[0]
            else:
                  content = message
                  sender = ''

      else:  
            thread_name = lines[0]
            sender = lines[0]
            content = message

      is_unread = any('Unread message' in line for line in lines)
      payload = {
            'thread_id': thread_id,
            'thread_name': thread_name,
            'unread': is_unread,
            'content': content,
            'is_group': is_group,
            'sender': sender,
            'timestamp': time.time()
      }
      return payload


chats = []

with sync_playwright() as p:
      context = p.chromium.launch_persistent_context(
      './messenger-session',
      headless=False,
      user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
      )
      page = context.new_page()
      page.goto("https://www.messenger.com")

      input("press any key to start")

      last_state = {}  # thread_id -> preview text

      print("listening...")

      while True:
            chats = []
            currentstate = []
            threads = page.query_selector_all('[role="row"]') #row: mga chat threads, i.e. user o gc
            for thread in threads:
                  data = parse_thread(thread)
                  if not data:
                        continue

                  currentstate.append({"name":data['thread_name'], 
                                       'unread':data['unread'], 
                                       'content':data['content'],
                                       'group':data['is_group'],
                                       'sender':data['sender'],
                                       'sent': round(data['timestamp'])
                                       })
                  
                  prev = last_state.get(data['thread_id'])
                  if prev != data['content']:
                        last_state[data['thread_id']] = data['content']
                        if prev is not None:
                              chats.append(data)
                              print(data)
                              #print(f"{data['name']!r}: {data['content']!r}, {'GROUP' if data['is_group'] else 'USER'}")

            requests.post('http://localhost:8000/event',json={"source":"messenger", "chats":chats, "currentstate":currentstate})                         
            time.sleep(1)


