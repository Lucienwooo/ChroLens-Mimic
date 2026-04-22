with open('ChroLens_Mimic.py', 'r', encoding='utf-8') as f:
    content = f.read()

main_block = """if __name__ == "__main__":
    # 正常啟動主程式
    app = RecorderApp()
    app.mainloop()"""

if main_block in content:
    content = content.replace(main_block, '')
    content += '\n\n' + main_block + '\n'
    
    with open('ChroLens_Mimic.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed indentation/placement')
else:
    print('main_block not found')
