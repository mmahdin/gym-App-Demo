from PySide6.QtCore import QPoint
from PySide6.QtCore import QPointF
from app_settings import *


region1 = [
    QPoint(171, 137), QPoint(169, 140), QPoint(
        166, 144), QPoint(162, 146),
    QPoint(160, 148), QPoint(156, 149), QPoint(
        153, 151), QPoint(150, 153),
    QPoint(146, 154), QPoint(143, 155), QPoint(
        140, 155), QPoint(137, 156),
    QPoint(134, 156), QPoint(130, 154), QPoint(
        126, 154), QPoint(123, 152),
    QPoint(120, 150), QPoint(118, 148), QPoint(
        117, 146), QPoint(115, 143),
    QPoint(113, 142), QPoint(115, 140), QPoint(
        118, 136), QPoint(120, 135),
    QPoint(124, 131), QPoint(125, 128), QPoint(
        127, 125), QPoint(128, 122),
    QPoint(129, 119), QPoint(131, 116), QPoint(
        133, 113), QPoint(134, 110),
    QPoint(137, 109), QPoint(141, 107), QPoint(
        145, 107), QPoint(148, 107),
    QPoint(150, 107), QPoint(153, 107), QPoint(
        157, 107), QPoint(160, 107),
    QPoint(163, 107), QPoint(164, 109), QPoint(
        167, 111), QPoint(168, 112),
    QPoint(170, 115), QPoint(170, 117), QPoint(
        171, 117), QPoint(172, 115),
    QPoint(173, 112), QPoint(175, 110), QPoint(
        179, 109), QPoint(183, 107),
    QPoint(186, 107), QPoint(189, 107), QPoint(
        191, 107), QPoint(193, 107),
    QPoint(197, 108), QPoint(200, 108), QPoint(
        203, 109), QPoint(206, 109),
    QPoint(208, 112), QPoint(210, 116), QPoint(
        213, 118), QPoint(214, 121),
    QPoint(216, 124), QPoint(217, 127), QPoint(
        218, 129), QPoint(220, 131),
    QPoint(221, 134), QPoint(223, 135), QPoint(
        225, 138), QPoint(226, 139),
    QPoint(228, 141), QPoint(229, 142), QPoint(
        227, 145), QPoint(225, 147),
    QPoint(222, 149), QPoint(217, 154), QPoint(
        212, 155), QPoint(208, 156),
    QPoint(205, 156), QPoint(202, 156), QPoint(
        198, 154), QPoint(194, 154),
    QPoint(189, 152), QPoint(186, 150), QPoint(
        182, 148), QPoint(178, 146),
    QPoint(175, 143), QPoint(174, 141), QPoint(172, 138)
]

region1 = [QPointF(p.x() * W_RATIO, p.y() * H_RATIO) for p in region1]

region2 = [QPoint(172, 47), QPoint(212, 199),
           QPoint(171, 267), QPoint(132, 196)]

region2 = [QPointF(p.x() * W_RATIO, p.y() * H_RATIO) for p in region2]
