import sys
from PyQt5 import QtWidgets, uic


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Load the UI Page
        uic.loadUi('main_window.ui', self)

        # Connect the signals.
        self.mask_add_pb.clicked.connect(self.add_mask_item)

    def add_mask_item(self, row, items):
        self.mask_table.setRowCount(self.mask_table.rowCount() + 1)
        self.mask_table.setItem(row, 0, QtWidgets.QTableWidgetItem(items[0]))
        self.mask_table.setItem(row, 1, QtWidgets.QTableWidgetItem(items[0]))
        self.mask_table.setItem(row, 2, QtWidgets.QTableWidgetItem(items[0]))
        self.mask_table.setItem(row, 3, QtWidgets.QTableWidgetItem(items[0]))



    # def create_voxelpart_object(self):
    #
    #     size = int(self.model_size_txt.text())
    #     dim = self.dim_combo.currentText()
    #     if dim == '2D':
    #         model_size = (size, size)
    #         elem_type = 'CPE4R'
    #     else:
    #         model_size = (size, size, size)
    #         elem_type = 'C3D8R'
    #
    #     # Create a part.
    #     part = vcams.voxelpart.VoxelPart(size=model_size, fill_value=1,
    #                                      voxel_size=(0.02, 0.02, 0.02),
    #                                      name='Filled %s Part' % dim,
    #                                      description='')
    #
    #     # Output the part.
    #     part.output_abaqus_inp(file_name='complete_part_%s' % dim,
    #                            elem_type=elem_type, dim=dim,
    #                            material_elem_sets=(1,), custom_elem_sets=True)
    #
    # def close_app(self):
    #     self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
