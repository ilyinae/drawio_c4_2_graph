import xml.etree.ElementTree as ET
import os

def cut_ancor_points(s): # очистка якорных точек в строке стиля
    l = s.split(';')
    for i in range(len(l)):
        if len(l[i])>7 and l[i][:7] == 'points=':
            l.remove(l[i])
            break
    return ';'.join(l)


def get_bb(g): # баундинг бокс для элемента (геометрии)
    bounding_rect = ((float(g.attrib['x']), float(g.attrib['y'])),(float(g.attrib['x'])+float(g.attrib['width']), float(g.attrib['y'])+float(g.attrib['height'])))
    return bounding_rect


def is_inside(rect1, rect2): # проверка на вхождение rect1 в rect2
   return rect1[0][0]>=rect2[0][0] and rect1[0][1]>=rect2[0][1] and rect1[1][0]<=rect2[1][0] and rect1[1][1]<=rect2[1][1]


def area(r): # площадь прямоугольника
    return (r[1][0] - r[0][0])*(r[1][1] - r[0][1])


def get_parents(root, elem): #Формирует строку имен родительских элементов в формате WB\ADS\Plattform\DataPlattform\DWH
    parent_dic, g = {}, elem.find('mxCell').find('mxGeometry')
    for e in root.findall('object'):
        if e.attrib['c4Type'] == 'SystemScopeBoundary':
            if is_inside(get_bb(g), get_bb(e.find('mxCell').find('mxGeometry'))):
                parent_dic[area(get_bb(e.find('mxCell').find('mxGeometry')))] = e.attrib['c4Name']
    if len(parent_dic)==0: return 'None'
    else: return '\\'.join(list(dict(sorted(parent_dic.items(),reverse=True)).values()))

def generate_graph_from_c4(file):
    new_elem_size = '60'

    tree = ET.parse(file, parser=None) # Создаем объект ElementTree из файла
    root = tree.getroot().find('diagram').find('mxGraphModel').find('root') # Получаем корневой элемент

    for elem in root.findall('object'):
        typ, geom, style = elem.attrib['c4Type'], elem.find('mxCell').find('mxGeometry'), elem.find('mxCell').attrib['style']

        match typ:
            case e if e in ("Software System", "Container", "Component"):
                style = style.replace('rounded=1', 'ellipse') # меняем системы, контейнеры и компоненты на круги
                geom.attrib['width'], geom.attrib['height'] = new_elem_size, new_elem_size  # меняем размер
                elem.attrib['label'] = '<font style="font-size: 16px"><b>%c4Name%</b></font>'  # меняем подпись
                elem.attrib['Parents'] = get_parents(root, elem)
            case "Person":
                geom.attrib['width'], geom.attrib['height'] = new_elem_size, new_elem_size  # меняем размер
                style = cut_ancor_points(style) # очищаем якорные точки
            case "hub":
                hub_id, many_list = elem.attrib['id'], list()
                for el in root.findall('object',):
                    if el.attrib['c4Type'] == "Relationship" and\
                    (el.find('mxCell').attrib['source'] == hub_id or el.find('mxCell').attrib['target']==hub_id):
                        if el.attrib['hub_order'] == 'one': # запоминаем целевой объект и
                            rep_obj = el.find('mxCell').attrib['source'] if el.find('mxCell').attrib['source'] != hub_id else el.find('mxCell').attrib['target']
                            rep_descr = el.attrib['c4Description'] # запоминаем описание
                            root.remove(el) # удаляем общую стрелку от хаба
                        elif el.attrib['hub_order'] == 'many': # формируем список связей для перетяжки
                            many_list.append(el.attrib['id'])
                for el in root.findall('object'):
                    if el.attrib['id'] in many_list: # перетягиваем связи к целевому объекту
                        if el.find('mxCell').attrib['source'] == hub_id: el.find('mxCell').attrib['source'] = rep_obj
                        if el.find('mxCell').attrib['target'] == hub_id: el.find('mxCell').attrib['target'] = rep_obj
                        if el.attrib['c4Description']=='': el.attrib['c4Description']=rep_descr # переносим описание из удаленной стрелки если его нет на перетягиваемой
                root.remove(elem) # удаляем хаб
            case "Relationship":
                style = style.replace('edgeStyle=orthogonalEdgeStyle', '')  # "выпрямляем" связи
                style +='strokeWidth=0.5;' # делаем их потоньше
                style += 'movable=0;resizable=0;rotatable=0;deletable=0;editable=0;locked=1;connectable=0' # и блокируем чтоб не сдвинуть случайно
                if geom.find('Array') is not None:  # удаляем искусственные точки связей
                    geom.remove(geom.find('Array'))

        style = style.replace('fontColor=#ffffff', 'fontColor=#000000') # меняем цвет подписи на черный
        elem.find('mxCell').attrib['style'] = style  #применяем стиль
    return tree


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    c4_filename = "Media_context_v2.0.drawio"
    c4_file = script_dir + "\\"+c4_filename
    out_file = c4_file.replace('.drawio', '_graph.drawio')
    generate_graph_from_c4(c4_file).write(out_file, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    main()
