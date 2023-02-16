import threading
import os
import fitz
from paddleocr import PaddleOCR

class OCRThread(threading.Thread):
    def __init__(self, page, img, lang, res):
        threading.Thread.__init__(self)
        self.page = page
        self.img = img
        self.lang = lang
        self.res = res

    def run(self):
        ocr = PaddleOCR(lang=self.lang)
        result = ocr.ocr(self.img)
        for line in result:
            text = line[1][0]
            rect = fitz.Rect(line[0][0][0], self.page.rect.height - line[0][0][3], line[0][0][2], self.page.rect.height - line[0][0][1])
            self.res.append((rect, text))


def ocr_pdf(pdf_file, lang='ch', num_threads=8):
    doc = fitz.open(pdf_file)
    all_results = []
    for pg in doc:
        if pg.number % 10 == 0:
            print(f"Processing page {pg.number + 1}...")
        img_list = pg.get_images()
        if not img_list:
            continue
        img_threads = []
        res = []
        for img in img_list:
            img_threads.append(OCRThread(pg, img[0], lang, res))
        for t in range(0, len(img_threads), num_threads):
            for img_thread in img_threads[t:t+num_threads]:
                img_thread.start()
            for img_thread in img_threads[t:t+num_threads]:
                img_thread.join()
        all_results.append(res)
    doc.close()
    return all_results

def recreate_pdf(pdf_file, ocr_results, output_file):
    doc = fitz.open(pdf_file)
    for pg_num, pg_results in enumerate(ocr_results):
        if not pg_results:
            continue
        pg = doc[pg_num]
        highlight = pg.new_highlight_annot
        highlight.update()
        for rect, text in pg_results:
            highlight = pg.new_highlight_annot
            highlight.rect = rect
            highlight.quadpoints = highlight.rect.to_quadpoints()
            highlight.update()
            highlight.info['content'] = text
            highlight.update()
    doc.save(output_file)
    doc.close()

if __name__ == '__main__':
    pdf_file = 'path/to/pdf'
    ocr_results = ocr_pdf(pdf_file)
    output_file = 'output.pdf'
    recreate_pdf(pdf_file, ocr_results, output_file)
    print(f"Finished. Output saved to {output_file}")
